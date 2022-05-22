from difflib import ndiff
from pathlib import Path
import os
import subprocess

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
	BarColumn(),
	TextColumn("{task.description}"),
	MofNCompleteColumn()
)
progress_group = Group(
	Panel(current_test_progress),
	overall_progress,
)

def test_cmd(cmd):
	# fix newline
	cmd = cmd.replace("\\n", "\n")

	# run cmd
	bash_output = subprocess.run(
		["bash"],
		capture_output=True,
		input=cmd.encode()
	).stdout.decode()
	minishell_output = subprocess.run(
		["./minishell"],
		capture_output=True,
		input=cmd.encode()
	).stdout.decode()

	# get cmd diff
	diff = ndiff(
		bash_output.splitlines(keepends=True),
		minishell_output.splitlines(keepends=True)
	)
	diff_output = ""
	diff_n = 0
	for d in diff:
		diff_n += 1
		diff_output += d

	return (
		Syntax(
			diff_output.removesuffix("\n"),
			lexer="diff",
			background_color="default"
		),
		Text("KO", style="red") if diff_n > 1 else Text("OK", style="green"))

def run_test(test_name, cmds, live, overall_task_id):
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
		show_header=False,
		show_lines=True,
		highlight=True
	)
	current_test_table.add_column(
		justify="center",
		vertical="middle"
	)
	current_test_table.add_column(
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
		live.console.log(f"testing: '{clean_cmd}'")
		diff = test_cmd(cmd)
		# add output to table
		current_test_table.add_row(
			Syntax(
				clean_cmd,
				background_color="default",
				lexer="bash"
			),
			diff[0],
			diff[1]
		)
		# increment progress if test is successful
		if (diff[1].plain == "OK"):
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

def checks():
	minishell = Path("./minishell")
	if minishell.exists():
		if os.access("./minishell", os.X_OK):
			return
		else:
			print("minishell is not executable!")
	else:
		print("minishell is missing!")
	exit(1)

def main():
	# verify that the minishell is present
	checks()
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
				run_test(test_file.name, cmds, live, overall_task_id)

		# stop overall progress bars
		overall_progress.update(
			overall_task_id,
			description="[bold]DONE[/bold]"
		)

if __name__=="__main__":
    main()
