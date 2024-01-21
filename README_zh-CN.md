# viscmd

## 介绍

Viscmd 的全称是 Visual Command, 旨在使输入 Linux 命令的过程更方便。 它提供了一个图形化的用户界面，使命令参数可视化，在界面上接收用户输入，
然后生成一个完整的命令行。

特性:
- 支持 bash 和 zsh
- 补全模式和运行模式
- 参数分组
- 内置类型 (file, directory, netdev, etc...)
- 支持使用多种语言来定义命令
- 命令版本匹配
- 复杂参数

## 安装

在 Deepin GNU/Linux 20.4 上开发, 应当能够在很多近年发布的 Linux 发行版上运行.

1. 确保安装了以下依赖:
- bash (5.0.3 tested)
- zsh (5.7.1-1 tested, optional)
- Python3 (3.7.3 tested) 
- python3-tk (3.7.3 tested) 

比如在 Debian/Ubuntu 上面安装: 
```shell
apt install -y python3-tk
```

2. 克隆或者下载本仓库代码：
```shell
git clone https://github.com/viscmd/viscmd.git
```

3. 以 root 用户运行 `install.sh`：
```shell
cd viscmd
sudo bash install.sh
```

4. 克隆 viscmd/data 仓库:
```shell
git clone https://github.com/viscmd/data.git /var/lib/viscmd
```

## 如何使用

### 补全模式

当我们已经处在 bash/zsh 中，先输入本软件支持的命令（见 viscmd/data 仓库），然后按 SHIFT-TAB。 例如: 

```shell
$ ls <SHIFT-TAB>
```

此时会弹出一个对话框：
![](assets/ls.png)

我们在这个对话框中填写一些参数，然后点击 OK 按钮。 我们会看到 bash/zsh 中命令补全完成。 

当然，此时我们需要按 ENTER 来运行这个被补全的命令。

### 运行模式

直接执行 `viscmd` 命令。 那个 OK 按钮变成 Run 按钮。 它会调用 `gnome-terminal` 
或者 `deepin-terminal` 来运行已经生成的命令。

## 问答
### 它不做什么
- 不解析命令行已经包含的参数。 
- 不校验输入的参数值的有效性。
- 不检查参数的约束（比如多个参数是否冲突）。

### 支持 macOS 吗
可能不行。 我没有Macbook。 

## 如何贡献

[请进一步阅读](CONTRIBUTING_zh-CN.md)
