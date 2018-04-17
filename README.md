# Notice
EC2 Scheduler has been superseded by [AWS Instance Scheduler](https://aws.amazon.com/answers/infrastructure-management/instance-scheduler/).

In 2016, the EC2 Scheduler was launched to help AWS customers easily configure custom start and stop schedules for their Amazon Elastic Compute Cloud (Amazon EC2) instances. In 2018, AWS launched [AWS Instance Scheduler](https://aws.amazon.com/answers/infrastructure-management/instance-scheduler/), a new and improved scheduling solution that enables customers to schedule Amazon EC2 instances, Amazon Relational Database Service (Amazon RDS) instances, and more. We encourage customers to migrate to AWS Instance Scheduler for future updates and new features.

Legacy templates, scripts, and documentation for EC2 Scheduler are available in this GitHub repository.

# ec2-scheduler

EC2 Scheduler is a simple AWS-provided solution that enables customers to easily configure custom start and stop schedules for their Amazon EC2 instances. The solution is easy to deploy and can help reduce operational costs for both development and production environments. 

Source code for the AWS solution "EC2 Scheduler". 


## Cloudformation templates

- cform/ec2-scheduler.template

## Lambda source code

- code/ec2-scheduler.py

***

Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/asl/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
