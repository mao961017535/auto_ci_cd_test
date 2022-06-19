[toc]

# 技术和依赖简介


## CI/CD简介
CI/CD 是一种通过在应用开发阶段引入自动化来频繁向客户交付应用的方法。
CI/CD 的核心概念是持续集成、持续交付和持续部署。

### 持续集成 CI
一旦开发人员对应用所做的更改被合并，系统就会通过自动构建应用并运行不同级别的自动化测试（通常是单元测试和集成测试）来验证这些更改，确保这些更改没有对应用造成破坏。
这意味着测试内容涵盖了从类和函数到构成整个应用的不同模块。如果自动化测试发现新代码和现有代码之间存在冲突，CI 可以更加轻松地快速修复这些错误。

简单理解成对某些重要分支的合并会触发对应的单元测试或集成测试，确保更改不对应用造成破坏。

### 持续交付或部署 CD
完成 CI 中的测试流程后，持续交付可自动将已验证的代码发布到存储库。
为了实现高效的持续交付流程，务必要确保 CI 已内置于开发管道。
持续交付的目标是拥有一个可随时部署到生产环境的代码库。持续部署作为持续交付的延伸将应用发布到生产环境。


### 参考项目(持续列出)
#### jenkins
#### drone
#### codo
#### spug

[使用 git 改善项目的协作](https://medium.com/flexisaf/git-workflow-for-your-project-3d9dbdc5f8e2) -- 提供一种工作流程，避免了 demo 适配不同工作流程带来太多的工作量。

[drone的pipeline原理与代码分析](https://www.cnblogs.com/xiaoqi/p/drone-pipeline.html) 帮助理解drone工作流程

[CI/CD是什么](https://www.redhat.com/zh/topics/devops/what-is-ci-cd)

[github OAuth文档](https://docs.github.com/cn/developers/apps/building-oauth-apps)

[github Webhooks文档](https://docs.github.com/en/github-ae@latest/developers/webhooks-and-events/webhooks)

# demo相关

## 主要流程
注册：
github注册OAuth应用填写应用ID和密钥 ---> 登陆系统获取 OAuth 授权 ---> 获取仓库列表 ---> 激活目标仓库

CI/CD
推送仓库 ---> github发送webhooks ---> 根据webhooks种类分配任务 ---> 活动的runner领取任务 ---> 注册容器 ---> 编译项目 ---> 测试 ---> 通知测试结果 ---> ………… ---> 销毁容器


## CI
大体参考Drone，部分参考OAuth。
对于本demo而言要完成的是
1. 获取代码仓库的信息；
2. 申请发送 webhooks ；
3. 用一个 CI 服务器接收 webhooks 并调度到对应的 runner；
4. runner进行编译和测试并通知编译结果。



### OAuth
通过 OAuth 模块获取仓库信息并注册webhook钩子监听推送。


## Webhooks监听
监听 Webhooks 决定后续执行内容。


### 简单前端页面
基于vue-template-admin和element-ui。

UI参考Drone和Jenkins。


### 任务与发布
一个集成过程称为一个任务，一个交付或部署称为一个发布。

任务通过启用目标仓库后监听webhook自动进行，交付或部署由目标仓库内配置文件和权限一起控制。


### 主机管理
#### 方案一
参考codo和spug,依赖docker，无须其他工具。
通过账号密码在目标主机增加ssh密钥后使用ssh连接进行管理。
可以将主机绑定到目标仓库下来进行后续的测试、交付或部署环节，少启动一个runner。
优点：
学习内容多，下一次分享或许有更多干货。
缺点：


#### 方案二
依托于 Kubernetes 集群来发布测试、交付和部署，主要工作量是和 Kubernetes Server通信。
优点：
略简单一些，强化 Kubernetes 学习。
缺点：
涉及知识点更少。

### 安全保障
弱项，边做边加


