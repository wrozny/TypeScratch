# TypeScratch
<p>Programming language that translates js-like code into .sb3 format that can be opened by Scratch</p>
<hr>

# !!! Work in progress
<p>
    The project is at stage of creating a translation layer
    between python and scratch
</p>
<div>
    You can currently create very simple scratch projects,
    but it gets very monotonic to do by hand with only straight compiler
    abstractions<br><br>Currently working:
    <ul>
        <li>Variables</li>
        <li>Math operators</li>
        <li>Control blocks</li>
        <li>Most if not all normal command blocks</li>
    </ul>
    <p>
        You can run main.py with python version 3.11 to generate the latest test.<br>
        This will generate .sb3 file inside <code>build/output/project_result.sb3</code> relative to the work directory
    </p>
</div>
<hr>

# Tasks in progress:
<ul>
    <li>Finishing the ScratchCompiler</li>
    <li>Defining IR (intermediate representation) format</li>
    <li>Making a project from IR with the compiler</li>
    <li>Parsing the language into AST (abstract syntax tree)</li>
    <li>Translating AST into IR</li>
    <li>Adding potential features that scratch doesn't provide by default like return types</li>
</ul>