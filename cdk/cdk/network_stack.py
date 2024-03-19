
from aws_cdk import (
    Stack,
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_route53 as r53,
)
from constructs import Construct

from cdk.util import settings, Props


class NetworkStack(Stack):
    backend_certificate: acm.ICertificate
    frontend_certificate: acm.ICertificate
    vpc: ec2.IVpc

    def __init__(
        self, scope: Construct, construct_id: str, props: Props, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Public and private subnets in to AZs
        self.vpc = ec2.Vpc(
            self,
            f"{settings.PROJECT_NAME}-vpc",
            availability_zones=['us-west-2a', 'us-west-2b'],
            cidr='10.0.0.0/16',
            subnet_configuration= [
                ec2.SubnetConfiguration(
                    name='PublicSubnet',
                    subnet_type= ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name='PrivateSubnet',
                    subnet_type= ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ]
        )

        self.backend_certificate = acm.Certificate(
            self,
            f"{settings.PROJECT_NAME}-backend-certificate",
            domain_name=settings.SUNET_DNS_ROOT,
            subject_alternative_names=[f"*.{settings.SUNET_DNS_ROOT}", f"*.final.{settings.SUNET_DNS_ROOT}"],
            validation=acm.CertificateValidation.from_dns(props.network_hosted_zone)
        )

        #Now us-west-2
        self.frontend_certificate = acm.DnsValidatedCertificate(
            self,
            f"{settings.PROJECT_NAME}-frontend-certificate",
            domain_name=settings.APP_DOMAIN,
            subject_alternative_names=[f"*.{settings.APP_DOMAIN}"],
            hosted_zone=props.network_hosted_zone,
            region="us-west-2",  
        )
