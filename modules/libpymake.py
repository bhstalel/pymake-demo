"""
    Handle targets, variables, ...
"""

from modules.yamlutils import YamlHandler
from typing import List
import logging
import sys
import os
import subprocess

PYMAKE_TARGET_SC = "$@"
PYMAKE_DEPS_ALL_SC = "$^"
PYMAKE_DEPS_FIRST_SC = "$<"

class PyMakeTarget:
    def __init__(self, name, value, variables):
        self.name = name
        self.command = value.get("cmd")
        self.variables = variables
        self.deps = value.get("dep")
        self.deps_count = self.count_deps()
        self.to_execute = True
        self.sanity()
        self.expand_command()
        self.expand_variables()

    """
        @FIXME: This will not work as the command is splitted by whitespaces
                This needs other suitable fix, I am done working on it for now ^^
    """
    def expand_variables(self):
        self.variables = [PyMakeVariable(var.name, self.expand_string(var.value)) \
                            for var in self.variables]

    def run(self):
        os.system(self.command)

    def count_deps(self) -> int:
        d_l = self.deps_list()
        return len(d_l) if d_l else 0

    def deps_list(self):
        if self.deps:
            l_dep = self.deps.split()
            logging.debug(f"[Target][{self.name}] Deps list: {l_dep}")
            return l_dep
        logging.debug(f"[Target][{self.name}] No dependencies!")
        return None

    def sanity(self):
        logging.debug(f"[Target][{self.name}] Doing sanity check ...")
        if not self.command:
            logging.error(f"[Target][{self.name}] No command specified for target: {name}")
            sys.exit(1)
        self.command = [cmd for cmd in self.command.split("\n")]

    def expand_string(self, s_plit) -> str:
        if s_plit.startswith("$(") and s_plit.endswith(")"):
            logging.debug(f"[Target][{self.name}] {s_plit} is a variable.")
            variable_name = s_plit[2:len(s_plit)-1]
            logging.debug(f"[Target][{self.name}] Name: {variable_name}")

            # Check if it is a special command
            var_split = variable_name.split()
            value = ""
            if len(var_split) > 1:
                if var_split[0] == "shell":
                    value = subprocess.getoutput(var_split[1])
                else:
                    logging.warn(f"Special custom command: {var_split[0]} not supported.")
            else:
                logging.debug(f"[Target][{self.name}] One variable: {var_split[0]}")
                value = [variable.value \
                        for variable in self.variables \
                        if variable.name == variable_name][0]

                if not value:
                    logging.debug(rf"[Target][{self.name}] Variable {variable_name} not found. In regular Makefile, this is usually ignored also.\n")

            # Expand variable
            logging.debug(f"[Target][{self.name}] Value: {value}")
            logging.debug(f"[Target][{self.name}] s_plit before: {s_plit}")
            s_plit = s_plit.replace(s_plit, value)
            logging.debug(f"[Target][{self.name}] s_plit after: {s_plit}")
        return s_plit

    """
        Expand the specified command

        Handle variables and special characters:
            - Varaible is in format: $(VAR)
            - Special characters:
                * $@
                * $^
                * $<
    """
    def expand_command(self):
        cmd_result = []
        for cmd in self.command:
            logging.debug(f"[Target][{self.name}] Expanding command: ({cmd})")
            cmd = cmd.replace(PYMAKE_TARGET_SC, self.name)

            if self.deps:
                cmd = cmd.replace(PYMAKE_DEPS_ALL_SC, self.deps)
                cmd = cmd.replace(PYMAKE_DEPS_FIRST_SC, self.deps)

            # Handle variables if exist : $(.*)
            s_plit_list = []
            for s_plit in cmd.split():
                logging.debug(f"[Target][{self.name}] Checking {s_plit} if it is a variable")
                s_plit = self.expand_string(s_plit)
                s_plit_list.append(s_plit)

            after_expansion = ' '.join(s_plit_list)
            logging.debug(f"[Target][{self.name}] Command after expansion: ({after_expansion})")
            cmd_result.append(after_expansion)
        self.command = cmd_result

class PyMakeVariable:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class PyMakeDep:
    def __init__(self, name, targets):
        self.name = name
        self.is_target = self.is_target(targets)
    
    def is_target(self, targets):
        return True if self.name in target else False

class PyMakeHandler:

    def __init__(self, path):
        # Load the yaml file
        self.yaml_handler = YamlHandler(path)
        self.content = self.yaml_handler.load()
        # Always load variable before targets
        self.vars = self.load_variables()
        self.variable_names = [variable.name for variable in self.vars]
        self.targets = self.load_targets()
        self.target_names = [target.name for target in self.targets]
        self.total_deps_count = self.count_total_deps()
        self.check_duplication()
        self.cmds_chain = []

    def count_total_deps(self) -> int:
        count = 0
        for target in self.targets:
            count += target.deps_count
        return count

    def chain_deps(self, deps_list):
        logging.debug(f"[deps] Handling : {deps_list}")
        deps = []

        if not deps_list:
            return

        for d in deps_list:
            logging.debug(f"[deps] Handling: {d}")
            target = self.get_target(d)
            # Is a file ?
            if not target:
                logging.warn(f"[Target][{d}] is not a target, maybe a file?, if yes check modification time, assuming changes!")
            else:
                self.cmds_chain.extend(target.command)
                deps.extend(target.deps_list())
        self.chain_deps(deps)

    """
        Run specified target
        If no target is provided, run first target found

        :param target: The target to run, default to None
    """
    def run(self, name=None):

        if not name:
            name = self.target_names[0]
        else:
            if not name in self.target_names:
                logging.error(f"*** No rule to make target {name}")
                sys.exit(1)

        # Load target
        target = self.get_target(name)
        logging.debug(f"# Checking target = {target.name}")
        logging.debug(f"# Deps            = {target.deps}")
        logging.debug(f"# Command         = {target.command}")

        self.cmds_chain.extend(target.command)

        # Handle dependencies
        if target.deps:
            self.chain_deps(target.deps_list())
            self.cmds_chain.reverse()
            logging.debug(f"Commands chain to execute {self.cmds_chain}")

        # Run commands
        for target_cmd in self.cmds_chain:
            logging.info(f"[MyMake] Excecuting: {target_cmd}")
            os.system(target_cmd)

    def get_target(self, name):
        for target in self.targets:
            if target.name == name:
                return target
        return None

    def check_duplication(self):
        if len(set(self.target_names)) != len(self.target_names):
            logging.error("There is duplication in targets!")
            sys.exit(1)

        if len(set(self.variable_names)) != len(self.variable_names):
            logging.error("There is duplication in variables!")
            sys.exit(1)

    def load_dep_of(self, name) -> dict:
        return get_target(name).deps

    def load_targets(self) -> list:
        targets = [ \
            PyMakeTarget(key, value, self.vars) \
            for (key, value) in self.content.items() \
            if type(value) == dict]
        if not targets:
            logging.error("*** No target is specified, nothing to do!")
            sys.exit(1)
        return targets

    def load_variables(self) -> list:
        return [PyMakeVariable(key, value) \
            for (key, value) in self.content.items() \
            if type(value) != dict]