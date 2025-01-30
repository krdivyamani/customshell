import os
import subprocess
import sys
import shlex
from cmd import Cmd

class CustomShell(Cmd):
    prompt = "$ "

    def __init__(self):
        super().__init__()
        self.builtins = {
            "exit": self.handle_exit,
            "echo": self.handle_echo,
            "type": self.handle_type,
            "pwd": self.handle_pwd,
            "cd": self.handle_cd
        }

    def locate_executable(self, command):
        path = os.environ.get("PATH", "")
        for directory in path.split(":"):
            file_path = os.path.join(directory, command)
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                return file_path

    def get_executables_in_path(self):
        executables = []
        path = os.environ.get("PATH", "")
        for directory in path.split(":"):
            if os.path.isdir(directory):
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                        executables.append(file)
        return executables

    def handle_exit(self, args):
        sys.exit(int(args[0]) if args else 0)

    def handle_echo(self, args):
        for i in range(len(args)):
            if args[i].startswith('"') and args[i].endswith('"'):
                args[i] = args[i][1:-1].replace('\\"', '"').replace('\\$', '$').replace('\\\\', '\\')
        print(" ".join(args))

    def handle_type(self, args):
        if args[0] in self.builtins:
            print(f"{args[0]} is a shell builtin")
        elif executable := self.locate_executable(args[0]):
            print(f"{args[0]} is {executable}")
        else:
            print(f"{args[0]} not found")

    def handle_pwd(self, args):
        print(os.getcwd())

    def handle_cd(self, args):
        if args:
            if args[0] == "~":
                os.chdir(os.environ["HOME"])
            elif os.path.isdir(args[0]):
                os.chdir(args[0]) # handles for relative path too
            else:
                print(f"cd: {args[0]}: No such file or directory")
        else:
            os.chdir(os.environ["HOME"])

    def do_exit(self, line):
        self.handle_exit(line.split())

    def do_echo(self, line):
        self.handle_echo(line.split())

    def do_type(self, line):
        self.handle_type(line.split())

    def do_pwd(self, line):
        self.handle_pwd(line.split())

    def do_cd(self, line):
        self.handle_cd(line.split())

    def complete_cd(self, text, line, begidx, endidx):
        return [d + ' ' for d in os.listdir('.') if os.path.isdir(d) and d.startswith(text)]

    def complete_echo(self, text, line, begidx, endidx):
        return ['echo ']

    def complete(self, text, state):
        buffer = self.get_executables_in_path() + list(self.builtins.keys())
        matches = [cmd for cmd in buffer if cmd.startswith(text)]
        return matches[state] + ' ' if state < len(matches) else None

    def default(self, line):
        parts = shlex.split(line)
        cmd, *args = parts

        if '>' in parts or '1>' in parts or '2>' in parts or '>>' in parts or '1>>' in parts or '2>>' in parts:
            if '2>>' in parts:
                idx = parts.index('2>>')
                cmd = parts[:idx]
                error_file = parts[idx + 1]
                with open(error_file, 'a') as f:
                    if cmd[0] in self.builtins:
                        original_stderr = sys.stderr
                        sys.stderr = f
                        self.builtins[cmd[0]](cmd[1:])
                        sys.stderr = original_stderr
                    elif executable := self.locate_executable(cmd[0]):
                        executable_name = os.path.basename(executable)
                        subprocess.run([executable_name, *cmd[1:]], stderr=f)
                    else:
                        f.write(f"{cmd[0]}: command not found\n")
            elif '2>' in parts:
                idx = parts.index('2>')
                cmd = parts[:idx]
                error_file = parts[idx + 1]
                with open(error_file, 'w') as f:
                    if cmd[0] in self.builtins:
                        original_stderr = sys.stderr
                        sys.stderr = f
                        self.builtins[cmd[0]](cmd[1:])
                        sys.stderr = original_stderr
                    elif executable := self.locate_executable(cmd[0]):
                        executable_name = os.path.basename(executable)
                        subprocess.run([executable_name, *cmd[1:]], stderr=f)
                    else:
                        f.write(f"{cmd[0]}: command not found\n")
            elif '>>' in parts or '1>>' in parts:
                if '>>' in parts:
                    idx = parts.index('>>')
                else:
                    idx = parts.index('1>>')
                cmd = parts[:idx]
                output_file = parts[idx + 1]
                with open(output_file, 'a') as f:
                    if cmd[0] in self.builtins:
                        original_stdout = sys.stdout
                        sys.stdout = f
                        self.builtins[cmd[0]](cmd[1:])
                        sys.stdout = original_stdout
                    elif executable := self.locate_executable(cmd[0]):
                        executable_name = os.path.basename(executable)
                        subprocess.run([executable_name, *cmd[1:]], stdout=f)
                    else:
                        f.write(f"{cmd[0]}: command not found\n")
            else:
                if '>' in parts:
                    idx = parts.index('>')
                else:
                    idx = parts.index('1>')
                cmd = parts[:idx]
                output_file = parts[idx + 1]
                with open(output_file, 'w') as f:
                    if cmd[0] in self.builtins:
                        original_stdout = sys.stdout
                        sys.stdout = f
                        self.builtins[cmd[0]](cmd[1:])
                        sys.stdout = original_stdout
                    elif executable := self.locate_executable(cmd[0]):
                        executable_name = os.path.basename(executable)
                        subprocess.run([executable_name, *cmd[1:]], stdout=f)
                    else:
                        f.write(f"{cmd[0]}: command not found\n")
        else:
            if cmd in self.builtins:
                self.builtins[cmd](args)
            elif executable := self.locate_executable(cmd):
                executable_name = os.path.basename(executable)
                subprocess.run([executable_name, *args])
            else:
                print(f"{cmd}: command not found")

if __name__ == "__main__":
    shell = CustomShell()
    shell.cmdloop()
