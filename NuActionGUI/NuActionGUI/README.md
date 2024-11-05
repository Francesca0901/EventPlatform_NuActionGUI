# NuActionGUI
A new version of the ActionGUI tool that does not make use of GUI models, but
rather relies on direct Python programming. 

## Getting started

### Prerequisites
To install NuActionGUI, you'll need:
- Python 3.6 or later
- pip 24.0 or later
- Java 22 or later

### Installation

To install NuActionGUI, you should:

- create a new Python virtual environment
```bash
python3 -m venv .venv
```

- activate the virtual environment
```bash 
source .venv/bin/activate
```

- install the required packages
```bash
cd src
pip install -r requirements.txt
```

- genrate model parsers
```bash
make grammars
```

- optionally, run the tests
```bash
make test
```

Note that OrderedSets are an experimental feature (hence some related tests may fail).


## Structure

The project is structured as follows:

- `src/`: contains the source code of the project
- `models/`: contains projects with some example (data, security, and privacy) models
- `resources/`: contains the resources used by the code generators

## Usage

To use NuActionGUI, you should:

- create a new project in the `models/` directory
- create new data security and privacy models the project directory
- run the code generator `src/genereate.py` with the project directory as argument

## License

This project is licensed under the MIT License - see the LICENSE file for details.
```


