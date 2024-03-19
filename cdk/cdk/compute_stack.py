import json
from aws_cdk import (
    Stack,
    Duration,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cloudfront_origins,
    aws_ec2 as ec2,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_logs as logs,
    aws_route53 as r53,
    aws_route53_targets as r53_targets,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_secretsmanager as secretsmanager,
    aws_ecr as ecr,
    aws_iam as iam
)
from constructs import Construct

from cdk.util import settings, Props


class ComputeStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props: Props, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Name Cluster Project
        cluster = ecs.Cluster(
            self, f"{settings.PROJECT_NAME}-cluster", vpc=props.network_vpc
        )

        #Define Fargate task with specifications as defined in tutorial
        fargate_task_definition = ecs.FargateTaskDefinition(
            self,
            f"{settings.PROJECT_NAME}-fargate-task-definition",
            cpu=1024,
            memory_limit_mib=3072,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )

        #Grant acess rights to Iam role
        props.data_aurora_db.secret.grant_read(fargate_task_definition.task_role)

        #get secrets to pass in information to wordpress
        db_secrets = {}
        for k,v in settings.DB_SECRET_MAPPING.items():
            db_secrets[k] = ecs.Secret.from_secrets_manager(props.data_aurora_db.secret, field=v)


        #Container for wordpress to run. Has healthcheck, logger, image from dockerhub, and secrets about database. 
        fargate_task_definition.add_container(
            f"{settings.PROJECT_NAME}-app-container",
            container_name=f"{settings.PROJECT_NAME}-app-container",
            health_check=ecs.HealthCheck(command=["CMD-SHELL", "curl -f -L http://localhost/index.php || exit 1"]),
            logging=ecs.AwsLogDriver(
                stream_prefix=f"{settings.PROJECT_NAME}-fargate",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            image=ecs.ContainerImage.from_registry("wordpress:latest"),
            port_mappings=[ecs.PortMapping(container_port=80, app_protocol=ecs.AppProtocol.http, name='http')],
            secrets =  db_secrets,
            environment = {
                "WORDPRESS_DB_HOST": props.data_aurora_db.cluster_endpoint.hostname,
            }
        )
 

        #ALB, redirects http, frontend TLS
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f"{settings.PROJECT_NAME}-fargate-service",
            cluster=cluster,
            domain_name='final.naveenkc.infracourse.cloud',
            certificate=props.network_frontend_certificate,
            redirect_http=True,
            domain_zone=props.network_hosted_zone,
            task_definition=fargate_task_definition,
        )

        #Bunch of errors here, fixed by letting all 200, 302, 301 redirects be healthy
        fargate_service.target_group.configure_health_check(
            path="/index.php",
            healthy_http_codes="200,302,301",  
        )

        #Changed for mysql
        fargate_service.service.connections.allow_to(
            props.data_aurora_db, ec2.Port.tcp(3306), "DB access"
        )


