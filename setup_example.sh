#!/usr/bin/env bash
set -e
# Title     : Script used as example to initialize ROGER
# Objective : Initializes a new ROGER instance with:
#             * Create SQL schema
#             * Import human, mouse and rat
#             * Create several GSE / DGE methods
# Created by: rcbiczok@gmail.com
roger init
# Add gene annotation data from other species
roger add-species "rnorvegicus_gene_ensembl" 10116
roger add-species "mmusculus_gene_ensembl" 10090