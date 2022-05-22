from difflib import ndiff
from pathlib import Path
import os
import subprocess
import argparse
from rich import (
    box,
    print
)
from rich.progress import (
	Progress,
    BarColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
	MofNCompleteColumn
)
from rich.console import Group
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax


current_test_progress = Progress(
	TimeElapsedColumn(),
	TextColumn("{task.description}"),
	MofNCompleteColumn()
)
overall_progress = Progress(
	TimeElapsedColumn(),
	BarColumn(bar_width=None),
	TextColumn("{task.description}", justify="center"),
	MofNCompleteColumn(),
	expand=True
)
progress_group = Group(
	Panel(current_test_progress),
	overall_progress
)

def get_diff(str1, str2):
	diff = ndiff(
		str1.splitlines(keepends=True),
		str2.splitlines(keepends=True)
	)

	diff_output = ""
	diff_n = 0
	for d in diff:
		if (d.startswith("- ") or d.startswith("+ ") or d.startswith("? ")):
			diff_n += 1
		if (len(diff_output) > 0):
			diff_output += "\n"
		diff_output += d.removesuffix("\n")

	return (diff_output, diff_n)

def test_cmd(minishell_path, cmd):
	# fix newline
	cmd = cmd.replace("\\n", "\n")

	# run cmd
	bash = subprocess.run(
		["bash"],
		capture_output=True,
		input=cmd.encode()
	)
	minishell = subprocess.run(
		[minishell_path],
		capture_output=True,
		input=cmd.encode()
	)

	# get diffs
	stdout_diff = get_diff(bash.stdout.decode(), minishell.stdout.decode())
	stderr_diff = get_diff(bash.stderr.decode(), minishell.stderr.decode())
	exit_code_diff = get_diff(str(bash.returncode), str(minishell.returncode))

	# check if test failed
	is_ok = True
	if stdout_diff[1] >= 1 or stderr_diff[1] >= 1 or exit_code_diff[1] >= 1:
		is_ok = False

	return (
		Syntax(
			stdout_diff[0].removesuffix("\n"),
			word_wrap=True,
			lexer="diff",
			background_color="default"
		),
		Syntax(
			stderr_diff[0].removesuffix("\n"),
			word_wrap=True,
			lexer="diff",
			background_color="default"
		),
		Syntax(
			exit_code_diff[0].removesuffix("\n"),
			word_wrap=True,
			lexer="diff",
			background_color="default"
		),
		Text("OK", style="green") if is_ok else Text("KO", style="red"))

def run_test(minishell_path, verbose, test_name, cmds, live, overall_task_id):
	# print test separator
	live.console.rule(f"'{test_name}' tests")

	# update overval progress bar
	overall_progress.update(
		overall_task_id,
		description=f"[bold]TESTING:[/bold] '{test_name}'"
	)
	# create current test progress var
	current_test_task = current_test_progress.add_task(
		description=f"[bold]TESTING:[/bold] '{test_name}'",
		total=len(cmds)
	)

	# create current test result table
	current_test_table = Table(
		box=box.ROUNDED,
		expand=True,
		show_lines=True,
		highlight=True,
	)
	current_test_table.add_column(
		"command",
		justify="center",
		vertical="middle"
	)
	current_test_table.add_column(
		"stdout",
		justify="center",
		vertical="middle"
	)
	current_test_table.add_column(
		"stderr",
		justify="center",
		vertical="middle"
	)
	current_test_table.add_column(
		"exit code",
		max_width=5,
		justify="center",
		vertical="middle"
	)
	current_test_table.add_column(
		justify="center",
		vertical="middle"
	)

	# test all cmds
	for cmd in cmds:
		clean_cmd = cmd.removesuffix("\n")
		# print logs
		if (verbose):
			live.console.log(f"testing: '{clean_cmd}'")
		diff = test_cmd(minishell_path, cmd)
		# add output to table
		current_test_table.add_row(
			Syntax(
				clean_cmd,
				word_wrap=True,
				background_color="default",
				lexer="bash"
			),
			diff[0],
			diff[1],
			diff[2],
			diff[3]
		)
		# increment progress if test is successful
		if (diff[3].plain == "OK"):
			current_test_progress.update(
				current_test_task,
				advance=1
			)

	# print test output table
	print(current_test_table)

	# stop & reset progress bars
	current_test_progress.stop_task(current_test_task)
	current_test_progress.update(
		current_test_task,
		description=f"[bold]DONE:[/bold] '{test_name}'",
	)
	overall_progress.update(
		overall_task_id,
		advance=1
	)

def verify_minishell(minishell_path):
	if minishell_path.exists():
		if minishell_path.is_file():
			if os.access(minishell_path.absolute(), os.X_OK):
				return minishell_path.absolute()
			else:
				print(f":warning: '[bold red]{minishell_path.absolute()}[/bold red]' is not executable!")
		else:
			print(f":warning: '[bold red]{minishell_path.absolute()}[/bold red]' is not a file!")
	else:
		print(f":warning: '[bold red]{minishell_path.absolute()}[/bold red]' does not exist!")
	exit(1)

def main():
	# parsre arguments
	parser = argparse.ArgumentParser(prog='test')
	parser.add_argument("minishell_path", help="path to your minishell executable", type=Path)
	parser.add_argument("-v", "--verbose", help="print tests logs", action="store_true")
	args = parser.parse_args()
	# verify that the minishell is present
	minishell_path = verify_minishell(args.minishell_path)
	with Live(progress_group) as live:
		# open tests dir
		tests_dir = Path('./tests')

		# get test files
		test_files = []
		for item in tests_dir.iterdir():
			if item.is_file():
				test_files.append(item)

		# create overval progress bar
		overall_task_id = overall_progress.add_task("", total=len(test_files))
	
		# loop overs each test file
		for test_file in test_files:
			with test_file.open('r' , encoding="utf-8") as file:
				# get all cmds
				cmds = file.readlines()
				# run test
				run_test(
					minishell_path,
					args.verbose,
					test_file.name,
					cmds,
					live,
					overall_task_id
				)

		# stop overall progress bars
		overall_progress.update(
			overall_task_id,
			description="[bold]DONE[/bold]"
		)

if __name__=="__main__":
    main()
