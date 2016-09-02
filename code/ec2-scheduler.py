######################################################################################################################
#  Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           #
#                                                                                                                    #
#  Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance        #
#  with the License. A copy of the License is located at                                                             #
#                                                                                                                    #
#      http://aws.amazon.com/asl/                                                                                    #
#                                                                                                                    #   
#  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES #
#  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    #
#  and limitations under the License.                                                                                #
######################################################################################################################


import boto3
import datetime
import json
from urllib2 import Request
from collections import Counter

def putCloudWatchMetric(region, instance_id, instance_state):
    
    cw = boto3.client('cloudwatch')

    cw.put_metric_data(
        Namespace='EC2Scheduler',
        MetricData=[{
            'MetricName': instance_id,
            'Value': instance_state,

            'Unit': 'Count',
            'Dimensions': [
                {
                    'Name': 'Region',
                    'Value': region
                }
            ]
        }]
        
    )

def lambda_handler(event, context):

    print "Running EC2 Scheduler"

    ec2 = boto3.client('ec2')
    cf = boto3.client('cloudformation')
    outputs = {}
    stack_name = context.invoked_function_arn.split(':')[6].rsplit('-', 2)[0]
    response = cf.describe_stacks(StackName=stack_name)
    for e in response['Stacks'][0]['Outputs']:
        outputs[e['OutputKey']] = e['OutputValue']
    ddbTableName = outputs['DDBTableName']

    awsRegions = ec2.describe_regions()['Regions']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(ddbTableName)
    response = table.get_item(
        Key={
            'SolutionName': 'EC2Scheduler'
        }
    )
    item = response['Item']



    # Reading Default Values from DynamoDB
    customTagName = str(item['CustomTagName'])
    customTagLen = len(customTagName)
    defaultStartTime = str(item['DefaultStartTime'])
    defaultStopTime = str(item['DefaultStopTime'])
    defaultTimeZone = 'utc'
    defaultDaysActive = str(item['DefaultDaysActive'])
    sendData = str(item['SendAnonymousData']).lower()
    createMetrics = str(item['CloudWatchMetrics']).lower()
    UUID = str(item['UUID'])
    TimeNow = datetime.datetime.utcnow().isoformat()
    TimeStamp = str(TimeNow)

    # Declare Dicts
    regionDict = {}
    allRegionDict = {}
    regionsLabelDict = {}
    postDict = {}  
    
    for region in awsRegions:
        try:
            # Create connection to the EC2 using Boto3 resources interface
            ec2 = boto3.resource('ec2', region_name=region['RegionName'])

            awsregion = region['RegionName']
            now = datetime.datetime.now().strftime("%H%M")
            nowMax = datetime.datetime.now() - datetime.timedelta(minutes=45)
            nowMax = nowMax.strftime("%H%M")
            nowDay = datetime.datetime.today().strftime("%a").lower()

            # Declare Lists
            startList = []
            stopList = []
            runningStateList = []
            stoppedStateList = []

            # List all instances
            instances = ec2.instances.all()

            print "Creating", region['RegionName'], "instance lists..."

            for i in instances:

                for t in i.tags:
                    if t['Key'][:customTagLen] == customTagName:

                        ptag = t['Value'].split(";")

                        # Split out Tag & Set Variables to default
                        default1 = 'default'
                        default2 = 'true'
                        startTime = defaultStartTime
                        stopTime = defaultStopTime
                        timeZone = defaultTimeZone
                        daysActive = defaultDaysActive
                        state = i.state['Name']
                        itype = i.instance_type

                        # Post current state of the instances
                        if createMetrics == 'enabled':
                            if state == "running":
                                putCloudWatchMetric(region['RegionName'], i.instance_id, 1)
                            if state == "stopped":
                                putCloudWatchMetric(region['RegionName'], i.instance_id, 0)

                        # Parse tag-value
                        if len(ptag) >= 1:
                            if ptag[0].lower() in (default1, default2):
                                startTime = defaultStartTime
                            else:
                                startTime = ptag[0]
                                stopTime = ptag[0]
                        if len(ptag) >= 2:
                            stopTime = ptag[1]
                        if len(ptag) >= 3:
                            timeZone = ptag[2].lower()
                        if len(ptag) >= 4:
                            daysActive = ptag[3].lower()

                        isActiveDay = False

                        # Days Interpreter
                        if daysActive == "all":
                            isActiveDay = True
                        elif daysActive == "weekdays":
                            weekdays = ['mon', 'tue', 'wed', 'thu', 'fri']
                            if (nowDay in weekdays):
                                isActiveDay = True
                        else:
                            daysActive = daysActive.split(",")
                            for d in daysActive:
                                if d.lower() == nowDay:
                                    isActiveDay = True

                        # Append to start list
                        if startTime >= str(nowMax) and startTime <= str(now) and \
                                isActiveDay == True and state == "stopped":
                            startList.append(i.instance_id)
                            print i.instance_id, " added to START list"
                            if createMetrics == 'enabled':
                                putCloudWatchMetric(region['RegionName'], i.instance_id, 1)

                        # Append to stop list
                        if stopTime >= str(nowMax) and stopTime <= str(now) and \
                                isActiveDay == True and state == "running":
                            stopList.append(i.instance_id)
                            print i.instance_id, " added to STOP list"
                            if createMetrics == 'enabled':
                                putCloudWatchMetric(region['RegionName'], i.instance_id, 0)

                        if state == 'running':
                            runningStateList.append(itype)
                        if state == 'stopped':
                            stoppedStateList.append(itype)

            # Execute Start and Stop Commands
            if startList:
                print "Starting", len(startList), "instances", startList
                ec2.instances.filter(InstanceIds=startList).start()
            else:
                print "No Instances to Start"

            if stopList:
                print "Stopping", len(stopList) ,"instances", stopList
                ec2.instances.filter(InstanceIds=stopList).stop()
            else:
                print "No Instances to Stop"


            # Built payload for each region
            if sendData == "yes":
                countRunDict = {}
                typeRunDict = {}
                countStopDict = {}
                typeStopDict = {}
                runDictType = {}
                stopDictType = {}   
                runDict = dict(Counter(runningStateList))
                for k, v in runDict.iteritems():
                    countRunDict['Count'] = v
                    typeRunDict[k] = countRunDict['Count']

                stopDict = dict(Counter(stoppedStateList))
                for k, v in stopDict.iteritems():
                    countStopDict['Count'] = v
                    typeStopDict[k] = countStopDict['Count']

                runDictType['instance_type'] = typeRunDict
                stopDictType['instance_type'] = typeStopDict

                typeStateSum = {}
                typeStateSum['running'] = runDictType
                typeStateSum['stopped'] = stopDictType
                StateSum = {}
                StateSum['instance_state'] = typeStateSum
                regionDict[awsregion] = StateSum
                allRegionDict.update(regionDict)
            
        except Exception as e:
            print ("Exception: "+str(e))
            continue

    # Build payload for the account
    if sendData == "yes":
        regionsLabelDict['regions'] = allRegionDict
        postDict['Data'] = regionsLabelDict
        postDict['TimeStamp'] = TimeStamp
        postDict['Solution'] = 'SO0002'
        postDict['UUID'] = UUID
        # API Gateway URL to make HTTP POST call
        url = 'https://metrics.awssolutionsbuilder.com/generic'
        data=json.dumps(postDict)
        headers = {'content-type': 'application/json'}
        req = Request(url, data, headers)

