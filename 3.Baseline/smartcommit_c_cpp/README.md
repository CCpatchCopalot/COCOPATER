## SmartCommit
We adapted [SmartCommit](https://github.com/Symbolk/SmartCommitCore) to C/C++ programming language.
## Dependencies
To run this project, you will need the following dependencies:

- **python**: 3.11.8

- **joern**: v4.0.250
The installation process for Joern can be found at https://docs.joern.io/installation.

- **tree-sitter**: 0.22.6
The installation process for tree-sitter can be found at https://tree-sitter.github.io/tree-sitter/

- Other relevant dependent packages listed in [requirements.txt](requirements.txt)

    To setup, run the following command:
    ```
    pip install -r requirements.txt
    ```
## How to Run
To run this tool, just modify the path of ctags CTAGS_PATH, the path of joern joern_path, the path of dataset excel_path in the lines 1-3 of the script config.py and run the script draw_diffhunk_graph.py in the following step:
```
python draw_diffhunk_graph.py
```