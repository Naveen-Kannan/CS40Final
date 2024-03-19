from aws_cdk import (
    Duration,
    Stack,
    aws_cloudfront as cloudfront,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_rds as rds,
    aws_s3 as s3,
)

from aws_solutions_constructs import aws_cloudfront_s3 as cfs3
from constructs import Construct

from cdk.util import settings, Props


class DataStack(Stack):
    aurora_db: rds.ServerlessCluster

    def __init__(
        self, scope: Construct, construct_id: str, props: Props, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Aurora serverless DB with MySQL for wordpress needs. Use private suibnet
        self.aurora_db = rds.ServerlessCluster(
            self,
            f"{settings.PROJECT_NAME}-aurora-serverless",
            engine=rds.DatabaseClusterEngine.AURORA_MYSQL, 
            default_database_name='final',  
            vpc=props.network_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            credentials=rds.Credentials.from_generated_secret(
                'wordpressuser',  
                exclude_characters=settings.DB_SPECIAL_CHARS_EXCLUDE
            ),
        )






 