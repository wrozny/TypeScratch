# TypeScratch
<p>Programming language that translates js-like code into .sb3 format that can be opened by Scratch</p>
<hr>

# !!! Work in progress
<p>
    Currently the only major unsupported features are lists and importing extensions,
    beside that and the fact that not all blocks are defined you can make anything 
    you could in the scratch app.
    I am currently in process of creating the parser and AST layer.
    
    Text -> Tokenizer -> Parser -> AST -> Builder -> Scratch Compiler -> Scratch File
</p>
<div>
    Currently working:
    <ul>
        <li>Variables</li>
        <li>Math operators</li>
        <li>Control blocks</li>
        <li>Procedures</li>
        <li>Reporters</li>
        <li>Most if not all normal command blocks</li>
    </ul>
    <p>
        You can run main.py with python version 3.11 to generate the latest test.<br>
        This will generate .sb3 file inside <code>build/output/project_result.sb3</code> relative to the work directory
    </p>
</div>
<hr>

# Tasks in progress:
<ol>
    <li>AST Layer (at least basic functionality)</li>
    <li>Parser Layer (creates AST)</li>
    <li>Builder Layer (translates AST into direct ScratchCompiler objects)</li>
    <li>Extending functionality compiler and language wise</li>
</ol>