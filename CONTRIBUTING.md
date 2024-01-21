
## Introduction

Each command is defined in a form of JSON file (in the [viscmd/data](https://github.com/viscmd/data) repo).

We need to write these files manually, or semi-automatically, and then test them manually. 

## JSON File Structure

```json
{
  "command": "command name",
  "show_version": "the shell command that shows the version of this command",
  "supported_versions": ["the version(s) supported by this file"],
  "arguments": [
    {...},
    ...
  ]
}
```

Each JSON object of the arguments list represents an argument.

The properties of an argument are as follows:
<table>
<thead>
<td>Property</td>
<td>Type</td>
<td>Explanation</td>
</thead>
<tr>
<td>keyword</td> <td>string</td> <td>Fixed parts of arguments, such as those that begin with a minus sign, such as -s</td>
</tr>
<tr>
<td>alias</td> <td>string</td> <td>As an alias for a keyword. For example, '-s/--size', we could use '-s' as a keyword and '--size' as an alias. </td>
</tr>
<tr>
<td>required</td> <td>boolean</td> <td>If this argument is required.</td>
</tr>
<tr>
<td>seperator</td> <td>string</td> <td>The seperator between a keyword and a value, usually a space or an equal sign</td>
</tr>
<tr>
<td>variable</td> <td>string</td> <td>A variable that represents the value of an argument.</td>
</tr>
<tr>
<td>type</td> <td>string</td> <td>The type of an argument value. See below.</td>
</tr>
<tr>
<td>choices</td> <td>list of string</td> <td>Possible argument values</td>
</tr>
<tr>
<td>default</td> <td>string</td> <td>Default argument value</td>
</tr>
<tr>
<td>group</td> <td>string</td> <td>Group name of this argument, defaults to empty</td>
</tr>
<tr>
<td>help</td> <td>string</td> <td>Help text</td>
</tr>
<tr>
<td>display_order</td> <td>integer</td> <td>Display order, the smaller the closer to the top</td>
</tr>
<tr>
<td>file_extensions</td> <td>list of string</td> <td>(Not commonly used) When type=='file', specifies the file name suffix.</td>
</tr>
<tr>
<td>one_of</td> <td>list of arguments</td> <td>(Not commonly used)Choose any one of a list of arguments</td>
</tr>
<tr>
<td>arguments</td> <td>list of arguments</td> <td>(Not commonly used)A sequence of arguments that have close relationship.</td>
</tr>
</table>


Types of an argument value：
<table>
<thead>
<td>Type</td>
<td>Explanation</td>
</thead>
<tr><td>file</td> <td>file for reading</td></tr>
<tr><td>savefile</td> <td>file for writing</td></tr>
<tr><td>directory</td> <td>directory</td></tr>
<tr><td>netdev</td> <td>network device</td></tr>
<tr><td>netns</td> <td>network namespace</td></tr>
<tr><td>bridge</td> <td>network bridge</td></tr>
<tr><td>blockdev</td> <td>block device</td></tr>
<tr><td>disk</td> <td>disk</td></tr>
<tr><td>localaddr</td> <td>local address</td></tr>
</table>

## Argument Examples
### A simplest argument
```text
--help
```
Using 'keyword' is enough:
```json
{
    "keyword": "--help"
}
```

### An argument with a value:
```text
--color=WHEN
```
We use 'variable' to represent the value:
```json
{
  "keyword": "--color",
  "variable": "WHEN",
  "seperator": "="
}
```
The 'seperator' defaults to space, if not given.

### Enumerable argument values

For values that are enumerable, put them in 'choices':

```json
 {
  "keyword": "--color",
  "variable": "WHEN",
  "choices": ["always", "auto", "never"],
  "seperator": "="
}
```

There is a special kind of argument that has values. For example:
```text
promisc { on | off }
```

We may treat the latter part as an argument value and give it a variable name. Such as:
```json
{
    "keyword": "promisc",
    "variable": "STATUS",
    "choices": ["on", "off"]
}
```

### Default agrument value

Use 'default' to give a default value:
```json
{
  "variable": "WHEN",
  "default": "always"
}
```

### Complex arguments

A sequence of multiply arguments:

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

Arguments that are mutually exclusive:

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

Nesting is supported, to describe more complex arguments.

## Auxiliary tools

### tools/convert_manpage.py

This small program attempts to parse the manual of the given command and generate a JSON file. Usage example:

```shell
tools/convert_manpage.py mkfs.vfat -o test.json
```

The resulting JSON file is not reliable and requires manual review and editing.
