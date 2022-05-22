# minishell_tester
An output tester for 42's minishell.

This tester will **only** check if the stdout, stderr and exit code of your `minishell` are the same as the ones from `bash`.

![screenshot of the tester](/assets/screenshot.png?raw=true "Screenshot of the tester")

## requirements
- python 3
- pip
- your minishell must be able to receive a command from the stdin without `readline`.

## how to use
```shell
./install
```
```shell
./test [-t test_name] [--verbose] </path/to/minishell_bin>
```
## credits
- https://github.com/simon-ameye/42-minishell_bash_tester_2022
- https://github.com/waxdred/tester_minishell42
