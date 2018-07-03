from cmapPy.pandasGEXpress.parse import parse as gct_parse
import pandas as pd
import os.path
import shutil

from roger.persistence.schema import DataSet
import roger.logic.geneanno
import roger.util
import roger.persistence.geneanno
from roger.exception import ROGERUsageError

DATASET_SUB_FOLDER = "dataset"


def parse_pheno_data(design_file, gct_data):
    design_data = pd.read_table(design_file, sep='\t', index_col=0)
    groups = design_data.apply(lambda row: "_".join(["%s.%d" % (key, value) for (key, value) in row.items()]), axis=1)
    pheno_data = pd.DataFrame({"Sample": list(gct_data.data_df)})

    pheno_data["_DatasetSampleIndex"] = range(1, pheno_data.shape[0] + 1)
    pheno_data["_Sample"] = list(gct_data.data_df)
    pheno_data["_SampleGroup"] = groups.values
    return pheno_data


def add_ds(session,
           roger_wd_dir,
           dataset_file,
           design_file,
           tax_id,
           symbol_type,
           exprs_type,
           ds_name,
           description,
           xref):
    # Input checking
    species_list = roger.persistence.geneanno.list_species(session)
    if species_list[species_list.TaxID == tax_id].empty:
        raise ROGERUsageError('Unknown taxon id: %s' % tax_id)

    if ds_name is None:
        ds_name = os.path.splitext(os.path.basename(dataset_file))[0]

    # Read and annotate data
    gct_data = gct_parse(file_path=dataset_file)
    pheno_data = parse_pheno_data(design_file, gct_data)
    print("Annotating features")
    (feature_data, annotation_version) = roger.logic.geneanno.annotate(session, gct_data, tax_id, symbol_type)

    print("Persisting data set")
    # Persist data
    datasets_path = os.path.join(roger_wd_dir, DATASET_SUB_FOLDER)
    dataset_path = os.path.join(datasets_path, ds_name)
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    exprs_file = os.path.abspath(os.path.join(dataset_path, "exprs.gct"))
    shutil.copy(dataset_file, exprs_file)

    pheno_file = os.path.abspath(os.path.join(dataset_path, "pheno.tsv"))
    pheno_data.to_csv(pheno_file, sep="\t")

    dataset_entry = DataSet(Name=ds_name,
                            GeneAnnotationVersion=annotation_version,
                            Description=description,
                            FeatureCount=feature_data.shape[0],
                            SampleCount=gct_data.data_df.shape[1],
                            ExprsWC=exprs_file,
                            ExprsSrc=exprs_file,
                            NormalizedExprsWC=exprs_file,
                            NormalizedExprsSrc=exprs_file,
                            ExprsType=exprs_type,
                            PhenoWC=pheno_file,
                            PhenoSrc=pheno_file,
                            #TODO
                            FeatureType="transcriptome",
                            TaxID=tax_id,
                            Xref=xref,
                            #TODO
                            URL="",
                            CreatedBy=roger.util.get_current_user_name(),
                            CreationTime=roger.util.get_current_datetime())
    session.add(dataset_entry)
    session.flush()
    feature_data["DataSetID"] = dataset_entry.ID
    session.commit()
    feature_data.to_sql("FeatureMapping", session.bind, if_exists='append', index=False)
    return dataset_entry
