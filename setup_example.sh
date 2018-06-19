#!/usr/bin/env bash
set -e
# Title     : Script used as example to initialize ROGER
# Objective : Initializes a new ROGER instance with:
#             * Create SQL schema
#             * Import human, mouse and rat
#             * Create several GSE / DGE methods
# Created by: rcbiczok@gmail.com
roger init-db
# Add gene annotation data from other species
roger add-species "rnorvegicus_gene_ensembl" 10116
roger add-species "mmusculus_gene_ensembl" 10090
# Add standard DGE methods
roger add-dge-method "limma" "limma" "3.30.6"
roger add-dge-method "edgeR" "edgeR" "3.16.4"
roger add-dge-method "DESeq2" "DESeq2" "1.14.1"
roger add-dge-method "voom+limma" "limma::voom+limma" "3.30.6"
# Add standard GSE methods
roger add-gse-method "camera" "limma::camera" "3.30.6"
roger add-gse-method "GSEA-P" "GSEA by gene permutation" "2.0.0"
roger add-gse-method "GSEA" "GSEA by sample permutation" "2.0.0"
roger add-gse-method "BioQC+limma" "ES of BioQC compared by limma" "1.2.0"
roger add-gse-method "GAGE" "GAGE" "2.24.0"
