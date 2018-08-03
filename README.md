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
   
# Adding annotation support for other species

After installation, ROGER can only consume expression data from human. You can use the `add-species` command add support for other
species in ROGER. For example, the following commands:

```bash
roger add-species "rnorvegicus_gene_ensembl" 10116
roger add-species "mmusculus_gene_ensembl" 10090
```

Would enable ROGER to consume data from rat and mouse as well. 
Internaly, ROGER will downlaod gene identifiers from the Ensembl BioMart service and assign them with internal identifiers
to allow efficient indexing.
   
# Example DGE analysis

Every data set used for the following examples can be found in [test_data](test_data).

## DGE Analysis with microarray data / limma:

1. Create a new microarray dataset:
    ```bash
    roger add-ds-ma test_data/ds/ma-example-signals.gct 10090 affy_mouse430_2
    ```
    This will add the normalized expression matrix "ma-example-signals.gct" to the database.
ROGER will automatically annotate the feature names inside the expression matrix based on the given
taxon id (here mouse) and feature symbol type (here AFFY Mouse430A 2 prope set). 
Additionally, ROGER will use the GCT file name as study name if nothing else is specified by parameter `--name`.
You can use `roger show-symbol-types 10090`  to see a list of supported feature types / probe sets

2. Add a design matrix
    ```bash
    roger add-design "test_data/ds/ma-example-design.txt" ma-example-signals
    ```
    Use `roger remove-design ma-example-design ma-example-signals` to remove the design matrix from `ma-example-signals`

3. Add a contrast matrix
    ```bash
    roger add-contrast test_data/ds/ma-example-contrast.txt ma-example-design ma-example-signals
    ```

4. Execute limma on added data set:
    ```bash
    roger run-dge-ma ma-example-contrast ma-example-design ma-example-signals
    ```

## DGE Analysis with RNAseq data / edgeR:

The DGE analysis for RNAseq data works similar compared to the DGE analysis for microarray data.
Only the commands for importing data sets and running the DGE analysis are different, 
because these commands provide slightly different optional parameters

```bash
roger add-ds-rnaseq test_data/ds/rnaseq-example-readCounts.gct 9606 entrezgene
roger add-design test_data/ds/rnaseq-example-DesignMatrix.txt rnaseq-example-readCounts
roger add-contrast test_data/ds/rnaseq-example-ContrastMatrix.txt rnaseq-example-DesignMatrix rnaseq-example-readCounts
roger run-dge-rnaseq rnaseq-example-ContrastMatrix rnaseq-example-DesignMatrix rnaseq-example-readCounts
```