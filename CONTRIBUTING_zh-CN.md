
## 介绍

每个命令是以 JSON 文件的形式定义的（在这个仓库 [viscmd/data](https://github.com/viscmd/data) ）。 

我们需要手动编写、或者半自动生成这些文件，然后手动测试。 

## JSON 文件结构

```json
{
  "command": "命令名称",
  "show_version": "显示版本号的命令",
  "supported_versions": ["本文件支持的版本"],
  "arguments": [ #参数列表
    {...},
    ...
  ]
}
```

参数列表的每一个 JSON 对象代表一个参数。

参数的属性如下：
<table>
<thead>
<td>属性名</td>
<td>类型</td>
<td>解释</td>
</thead>
<tr>
<td>keyword</td> <td>string</td> <td>参数的固定部分，比如以减号开头的部分，比如-s</td>
</tr>
<tr>
<td>alias</td> <td>string</td> <td>作为关键字的别名。例如'-s/--size'，我们可以用'-s'作为关键字，同时用'--size'作为别名。</td>
</tr>
<tr>
<td>required</td> <td>boolean</td> <td>是否必填</td>
</tr>
<tr>
<td>seperator</td> <td>string</td> <td>关键字与值的分隔符，一般是空格或者等于号</td>
</tr>
<tr>
<td>variable</td> <td>string</td> <td>代表参数值的变量</td>
</tr>
<tr>
<td>type</td> <td>string</td> <td>参数值的类型，见下文</td>
</tr>
<tr>
<td>choices</td> <td>list of string</td> <td>可能的参数值</td>
</tr>
<tr>
<td>default</td> <td>string</td> <td>默认的参数值</td>
</tr>
<tr>
<td>group</td> <td>string</td> <td>本参数的组名，默认为空</td>
</tr>
<tr>
<td>help</td> <td>string</td> <td>帮助文字</td>
</tr>
<tr>
<td>display_order</td> <td>integer</td> <td>显示顺序，越小越靠前</td>
</tr>
<tr>
<td>file_extensions</td> <td>list of string</td> <td>（不常用）当type=='file'时，指定文件名后缀</td>
</tr>
<tr>
<td>one_of</td> <td>参数列表</td> <td>（不常用）一组参数任选其一</td>
</tr>
<tr>
<td>arguments</td> <td>参数列表</td> <td>（不常用）具有密切关系的参数序列</td>
</tr>
</table>


参数值的类型：
<table>
<thead>
<td>类型</td>
<td>解释</td>
</thead>
<tr><td>file</td> <td>用于读取的文件</td></tr>
<tr><td>savefile</td> <td>用于保存的文件</td></tr>
<tr><td>directory</td> <td>目录</td></tr>
<tr><td>netdev</td> <td>网络设备</td></tr>
<tr><td>netns</td> <td>网络命名空间</td></tr>
<tr><td>bridge</td> <td>网桥</td></tr>
<tr><td>blockdev</td> <td>块设备</td></tr>
<tr><td>disk</td> <td>磁盘</td></tr>
<tr><td>localaddr</td> <td>本地地址</td></tr>
</table>

## 参数示例

### 最简单的参数
```text
--help
```
使用 keyword 即可:
```json
{
    "keyword": "--help"
}
```

### 有值的参数
```text
--color=WHEN
```
我们使用 variable 代表参数值；seperator 代表分隔符：
```json
{
  "keyword": "--color",
  "variable": "WHEN",
  "seperator": "="
}
```
seperator 如果没有指定，就缺省为空格。

### 可枚举的参数值
如果参数值是可枚举的，那么用 choices 指定这些值。例如：
```json
 {
  "keyword": "--color",
  "variable": "WHEN",
  "choices": ["always", "auto", "never"],
  "seperator": "="
}
```

有一种特殊风格的参数，例如：
```text
promisc { on | off }
```

可以将后一部分看做参数值，并且给它命名一个变量。例如：
```json
{
    "keyword": "promisc",
    "variable": "STATUS",
    "choices": ["on", "off"]
}
```

### 缺省的参数值
使用 default 指定缺省值：
```json
{
  "variable": "WHEN",
  "default": "always"
}
```

### 复杂的参数

包含多个参数的序列:

```json
{
  "arguments": [
    {
      "keyword": "--extract"
    },
    {
      "variable": "archive",
      "help": "The archive to extract"
    },
    {
      "variable": "dest",
      "help": "The destination directory"
    }
  ]
}
```

互斥的参数:

```json
{
  "one_of": [
    {
      "keyword": "add"
    },
    {
      "keyword": "delete"
    },
    {
      "keyword": "show"
    }
  ]
}
```

支持嵌套，以描述更加复杂的参数。

## 辅助工具

### tools/convert_manpage.py

这个小程序尝试解析给定的命令的手册，生成一个 JSON 文件。 用法举例：

```shell
tools/convert_manpage.py mkfs.vfat -o test.json
```

生成的 JSON 文件不是很靠谱，需要人工检查和编辑。
