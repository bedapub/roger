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
ROGER_DATA_FOLDER="some_folder" #default is /tmp or other temporary directory
```
5. Initialize ROGER with the following command:
```bash
roger init
```
6. Populate ROGER with additional data by using its command line interface. See [setup_example.sh](setup_example.sh) for more information
7. Install additional R packages:
    1. ribiosROGER, ribiosIO and ribiosExpression from [RIBIOS](https://github.com/Accio/ribios)
    2. [Bioconductor](https://www.bioconductor.org/) and the [limma](https://bioconductor.org/packages/release/bioc/html/limma.html) package.
    
# Example DGE analysis

You can find an example data set in the folder [test_data](test_data).
1. Import data set from GCT files to ROGER
```bash
roger add-ds ./test_data/gct/GSE93720.RMA.collapsed.gct ./test_data/dge/GSE93720_design.txt 9606 external_gene_name
```
2. Run DGE analysis of inserted data set
```bash
roger run-dge limma GSE93720.RMA.collapsed ./test_data/dge/GSE93720_design.txt ./test_data/dge/GSE93720_contrast.txt
```