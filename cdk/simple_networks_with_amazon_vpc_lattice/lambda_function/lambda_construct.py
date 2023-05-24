from aws_cdk import RemovalPolicy, Stack, aws_ec2, aws_iam, aws_lambda
from aws_cdk.aws_iam import Policy
from aws_cdk.aws_lambda_python_alpha import PythonLayerVersion
from constructs import Construct


class LambdaConstruct(Construct):

    def __init__(self, scope: Construct, id_: str) -> None:
        super().__init__(scope, id_)
        self.id_ = id_
        self.scope = scope

        self.stack = Stack.of(self)
        self.region = self.stack.region
        self.account_id = self.stack.account

        self.lambda_vpc = self._build_lambda_vpc()
        self.lambda_layer = self._build_common_layer()
        self.lambda_role = self._build_lambda_role()
        self.lambda_function = self._build_lambda()

    def _build_lambda_vpc(self) -> aws_ec2.Vpc:
        return aws_ec2.Vpc(
            self, 'LambdaVpc', ip_addresses=aws_ec2.IpAddresses.cidr('10.0.0.0/16'), max_azs=2, nat_gateways=1, subnet_configuration=[
                aws_ec2.SubnetConfiguration(name='LambdaPublicSubnet', subnet_type=aws_ec2.SubnetType.PUBLIC, cidr_mask=24),
                aws_ec2.SubnetConfiguration(name='LambdaPrivateSubnet', subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24)
            ])

    def _build_lambda_role(self) -> aws_iam.Role:
        role = aws_iam.Role(
            self,
            'LambdaRole',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name=('service-role/AWSLambdaBasicExecutionRole'))
            ],
        )
        vpc_policy_document = aws_iam.PolicyDocument(statements=[
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=["ec2:DescribeNetworkInterfaces"],
                resources=["*"],
            ),
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=["ec2:CreateNetworkInterface"],
                resources=["*"],
            ),
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=["ec2:DeleteNetworkInterface"],
                resources=["*"],
            ),
        ])

        policy = Policy(self, 'LambdaPolicy', document=vpc_policy_document)
        role.attach_inline_policy(policy)

        return role

    def _build_common_layer(self) -> PythonLayerVersion:
        return PythonLayerVersion(
            self,
            'LambdaCommonLayer',
            entry='.build/common_layer',
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_10],
            removal_policy=RemovalPolicy.DESTROY,
        )

    def _build_lambda(self) -> aws_lambda.Function:
        return aws_lambda.Function(
            self,
            'LambdaFunction',
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset('.build/lambdas/'),
            handler='lambda_handlers.lambda_function.handle',
            retry_attempts=0,
            layers=[self.lambda_layer],
            vpc=self.lambda_vpc,
            vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
            role=self.lambda_role,
        )
