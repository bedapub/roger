# ROGER
Understand gene expression regulation with ROGER (Roche Omnibus of Gene Expression Regulation)

# Software requirements
* Python 3 or greater

# Instalaltion
1. Install Python 3 (https://www.python.org/downloads/) on your system or create an virtual environment
2. Clone this repository to your preferred ROGER installation directory
```bash
git clone git@github.com:bedapub/roger.git
```
3. Switch to the cloned root directory of ROGER and install ROGER through `pip`:
```bash
pip install -e .
```
4. Create a configuration file called `.roger_config.cfg` in your user home directory and add your [SQLAlchemy](https://www.sqlalchemy.org) property there. 
An example configuration file could look like this:
```python
# http://docs.sqlalchemy.org/en/latest/core/engines.html
SQLALCHEMY_DATABASE_URI="sqlite:///roger-schema.db"
```
5. Initialize ROGER with the following command:
```bash
roger init
```
6. Populate ROGER with additional data by using its command line interface. See [setup_example.sh](setup_example.sh) for more information
