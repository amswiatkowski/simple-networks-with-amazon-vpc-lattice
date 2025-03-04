from aws_cdk import Stack, aws_ec2, aws_ecs, aws_elasticloadbalancingv2, aws_iam
from constructs import Construct


# pylint: disable=too-many-instance-attributes
class EcsConstruct(Construct):

    def __init__(self, scope: Construct, id_: str) -> None:
        super().__init__(scope, id_)
        self.id_ = id_
        self.scope = scope

        self.stack = Stack.of(self)
        self.region = self.stack.region
        self.account_id = self.stack.account

        self.ecs_vpc = self._build_ecs_vpc()

        self.ecs_execution_role = self._create_ecs_execution_role()
        self.ecs_task_role = self._create_ecs_task_role()

        self.ecs_cluster = self._build_ecs_cluster()
        self.fargate_task = self._build_fargate_task()
        self.container = self._add_container_to_the_task()
        self._add_port_mapping()
        self.fargate_service = self._build_fargate_service()

        self.alb_security_group = self._build_alb_security_group()
        self.alb = self._build_alb_for_fargate_service()
        self._add_listener_to_alb()

    def _build_ecs_vpc(self) -> aws_ec2.Vpc:
        return aws_ec2.Vpc(
            self, 'EcsVpc', ip_addresses=aws_ec2.IpAddresses.cidr('10.0.0.0/16'), max_azs=2, nat_gateways=1, subnet_configuration=[
                aws_ec2.SubnetConfiguration(name='EcsPublicSubnet', subnet_type=aws_ec2.SubnetType.PUBLIC, cidr_mask=24),
                aws_ec2.SubnetConfiguration(name='EcsPrivateSubnet', subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24)
            ])

    def _build_ecs_security_group(self) -> aws_ec2.SecurityGroup:
        security_group = aws_ec2.SecurityGroup(
            self,
            'EcsSG',
            vpc=self.ecs_vpc,
            allow_all_outbound=None,
        )

        return security_group

    def _create_ecs_execution_role(self) -> aws_iam.Role:
        role = aws_iam.Role(self, 'EcsExecutionRole', assumed_by=aws_iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
                            role_name="ecs-execution-role")

        role.add_to_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW, actions=[
                    'elasticloadbalancing:DeregisterInstancesFromLoadBalancer', 'elasticloadbalancing:DeregisterTargets',
                    'elasticloadbalancing:Describe*', 'elasticloadbalancing:RegisterInstancesWithLoadBalancer',
                    'elasticloadbalancing:RegisterTargets', 'ec2:Describe*', 'ec2:AuthorizeSecurityGroupIngress', 'sts:AssumeRole'
                ], resources=["*"]))
        return role

    def _create_ecs_task_role(self) -> aws_iam.Role:
        role = aws_iam.Role(self, 'EcsTaskRole', assumed_by=aws_iam.ServicePrincipal('ecs-tasks.amazonaws.com'), role_name="ecs-task-role")

        # Setup Role Permissions
        role.add_to_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW, actions=[
                    'ecr:GetAuthorizationToken', 'ecr:BatchCheckLayerAvailability', 'ecr:GetDownloadUrlForLayer', 'ecr:BatchGetImage',
                    'logs:CreateLogStream', 'logs:PutLogEvents'
                ], resources=["*"]))

        return role

    def _build_ecs_cluster(self) -> aws_ecs.Cluster:
        return aws_ecs.Cluster(self, 'EcsCluster', vpc=self.ecs_vpc)

    def _build_fargate_task(self) -> aws_ecs.FargateTaskDefinition:
        return aws_ecs.FargateTaskDefinition(self, 'EcsFargateTask', cpu=256, memory_limit_mib=512, execution_role=self.ecs_execution_role,
                                             task_role=self.ecs_task_role)

    def _add_container_to_the_task(self) -> aws_ecs.ContainerDefinition:
        return self.fargate_task.add_container('EcsContainer', image=aws_ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"))

    def _add_port_mapping(self) -> None:
        self.container.add_port_mappings(aws_ecs.PortMapping(container_port=80, host_port=80, protocol=aws_ecs.Protocol.TCP))

    def _build_alb_security_group(self) -> aws_ec2.SecurityGroup:
        security_group = aws_ec2.SecurityGroup(
            self,
            'EcsAlbSG',
            vpc=self.ecs_vpc,
            allow_all_outbound=None,
        )
        security_group.add_ingress_rule(peer=aws_ec2.Peer.any_ipv4(), connection=aws_ec2.Port.tcp(80))

        return security_group

    def _build_alb_for_fargate_service(self) -> aws_elasticloadbalancingv2.ApplicationLoadBalancer:
        load_balancer = aws_elasticloadbalancingv2.ApplicationLoadBalancer(
            self, 'EcsALB', vpc=self.ecs_vpc, internet_facing=False,
            vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC), security_group=self.alb_security_group)
        aws_elasticloadbalancingv2.ApplicationTargetGroup(self, 'EcsALBDefaultTargetGroup', port=80,
                                                          protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTP, vpc=self.ecs_vpc)
        return load_balancer

    def _build_fargate_service(self) -> aws_ecs.FargateService:
        return aws_ecs.FargateService(self, "EcsFargateService", task_definition=self.fargate_task, cluster=self.ecs_cluster,
                                      desired_count=1, service_name="ecs-service")

    def _add_listener_to_alb(self) -> None:
        alb_listener = self.alb.add_listener('EcsAlbListener', port=80, open=False,
                                             protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTP)

        alb_listener.add_targets('ECS', port=80, targets=[self.fargate_service])
