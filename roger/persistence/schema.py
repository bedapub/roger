from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Enum
from sqlalchemy import ForeignKey, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from pandas import read_table, DataFrame
import enum

from roger.persistence import db
from roger.persistence.json_backport import RogerJSON
import roger.util

DEFAULT_STR_SIZE = 64
STR_PATH_SIZE = 256
STR_DESC_SIZE = STR_PATH_SIZE


class ExprsType(enum.Enum):
    MICRO_ARRAY = 1
    RNA_SEQ = 2


class MicroArrayType(enum.Enum):
    RMA = 1
    MAS5 = 2


class RNASeqType(enum.Enum):
    RPKMS = 1


class GeneAnnotation(db.Model):
    __tablename__ = 'GeneAnnotation'

    RogerGeneIndex = Column(Integer, primary_key=True)
    # TODO: Version flushing not easy, need to make
    # Option 1) Make an entire Version Mapping
    # Option 2) Make an incremental invalidation of changed / removed genes
    Version = Column(String(DEFAULT_STR_SIZE), nullable=False)
    TaxID = Column(Integer, nullable=False)
    # ALWAYS means stable Ensembl gene ID without version (.x)
    EnsemblGeneID = Column(String(DEFAULT_STR_SIZE))
    # NCBI Gene ID
    EntrezGeneID = Column(Integer)
    GeneType = Column(String(DEFAULT_STR_SIZE))
    GeneSymbol = Column(String(DEFAULT_STR_SIZE), index=True)
    IsObsolete = Column(Boolean, nullable=False)

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<GeneAnnotation(RogerGeneIndex='%s', Version='%s', TaxID='%s', EnsemblGeneID='%s', EntrezGeneID='%s'," \
               " GeneSymbol='%s', IsObsolete='%s')>" \
               % (self.RogerGeneIndex, self.Version, self.TaxID,
                  self.EnsemblGeneID, self.EntrezGeneID, self.GeneSymbol, self.IsObsolete)


class Ortholog(db.Model):
    __tablename__ = 'Ortholog'

    RogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex, ondelete="CASCADE"), primary_key=True)
    HumanRogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex), primary_key=True)

    Gene = relationship("GeneAnnotation", foreign_keys="[Ortholog.HumanRogerGeneIndex]")

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<Ortholog(RogerGeneIndex='%s', HumanRogerGeneIndex='%s')>" \
               % (self.RogerGeneIndex, self.HumanRogerGeneIndex)


class GeneSetCategory(db.Model):
    __tablename__ = 'GeneSetCategory'

    ID = Column(Integer, primary_key=True)
    Name = Column(String(DEFAULT_STR_SIZE), unique=True, nullable=False)
    FileWC = Column(String(STR_PATH_SIZE), nullable=False)
    FileSrc = Column(String(STR_PATH_SIZE), nullable=False)

    GeneSets = relationship("GeneSet", back_populates="Category")

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<GeneSetCategory(ID='%s', Name='%s')>" \
               % (self.ID, self.Name)


class GeneSet(db.Model):
    __tablename__ = 'GeneSet'

    ID = Column(Integer, primary_key=True)
    CategoryID = Column(Integer, ForeignKey(GeneSetCategory.ID, ondelete="CASCADE"), nullable=False)
    Name = Column(String(STR_DESC_SIZE), nullable=False)
    # Behaviour: If TaxID == HumanTaxID then use RogerGeneIndex from this GeneSet. Else convert to human GeneSets first
    TaxID = Column(Integer, nullable=False)
    Description = Column(String(STR_DESC_SIZE))
    GeneCount = Column(Integer, nullable=False)
    # True if geneset is supposed to be internal
    IsPrivate = Column(Boolean, nullable=False)
    # Can point to reference geneset Information (e.g. in MongoDB)
    URL = Column(String(DEFAULT_STR_SIZE))

    Category = relationship("GeneSetCategory", back_populates="GeneSets")
    Genes = relationship("GeneSetGene", back_populates="GeneSet")

    __table_args__ = (
        UniqueConstraint(CategoryID, Name, name='GeneSetName'),
        {'mysql_engine': 'InnoDB'}
    )

    def __repr__(self):
        return "<GeneSet(ID='%s', CategoryID='%s', Name='%s', TaxID='%s', Description='%s', GeneCount='%s'," \
               "IsPrivate='%s', URL='%s')>" \
               % (self.ID, self.CategoryID, self.Name, self.TaxID, self.Description,
                  self.GeneCount, self.IsPrivate, self.URL)


# TODO: make this a regular table object, not a full-blown class
class GeneSetGene(db.Model):
    __tablename__ = 'GeneSetGene'

    GeneSetID = Column(Integer, ForeignKey(GeneSet.ID, ondelete="CASCADE"), primary_key=True)
    RogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex), primary_key=True)
    # TODO: Can be computed on the fly by the same mechanism as in Genesets.TaxID, but requires one less JOIN
    # HumanRogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex), primary_key=True)

    GeneSet = relationship("GeneSet", back_populates="Genes")
    Gene = relationship("GeneAnnotation", foreign_keys=[RogerGeneIndex])

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<GeneSetGene(GeneSetID='%s', RogerGeneIndex='%s')>" \
               % (self.GeneSetID, self.RogerGeneIndex)


class DataSet(db.Model):
    __tablename__ = 'DataSet'

    Type = Column(Enum(ExprsType), nullable=False)
    ID = Column(Integer, primary_key=True)
    Name = Column(String(DEFAULT_STR_SIZE), unique=True, nullable=False)
    # To ensure that analysis is reproducible when loading new gene annotations into database
    GeneAnnotationVersion = Column(String(DEFAULT_STR_SIZE), nullable=False)
    Description = Column(String(STR_DESC_SIZE))
    FeatureCount = Column(Integer, nullable=False)
    SampleCount = Column(Integer, nullable=False)
    # Path to working copy of GCT file
    ExprsWC = Column(String(STR_PATH_SIZE), nullable=False)
    # Path to external / save copy of GCT file
    ExprsSrc = Column(String(STR_PATH_SIZE), nullable=False)
    # Path to working copy of TDF file
    PhenoWC = Column(String(STR_PATH_SIZE), nullable=False)
    # Path to external / save copy of TDF file
    PhenoSrc = Column(String(DEFAULT_STR_SIZE))
    TaxID = Column(Integer, nullable=False)
    Xref = Column(String(DEFAULT_STR_SIZE))
    CreatedBy = Column(String(DEFAULT_STR_SIZE), nullable=False)
    CreationTime = Column(DateTime, nullable=False)

    __table_args__ = {'mysql_engine': 'InnoDB'}

    __mapper_args__ = {
        'polymorphic_on': Type
    }

    def __repr__(self):
        return "<DataSet(ID='%s', Name='%s' Type='%s')>" \
               % (self.ID, self.Name, self.Type)

    @hybrid_property
    def exprs_data(self):
        return roger.util.parse_gct(self.ExprsWC)

    @hybrid_property
    def pheno_data(self):
        return read_table(self.PhenoWC, sep='\t', index_col=0)

    @hybrid_property
    def feature_data(self):
        return roger.util.as_data_frame(FeatureMapping.query
                                        .add_columns(GeneAnnotation.GeneSymbol)
                                        .outerjoin(GeneAnnotation,
                                                   FeatureMapping.RogerGeneIndex == GeneAnnotation.RogerGeneIndex)
                                        .filter(FeatureMapping.DataSetID == self.ID)
                                        .order_by(FeatureMapping.FeatureIndex))

    @hybrid_property
    def dge_models(self):
        return DGEmodel.query \
            .filter(Contrast.DesignID == Design.ID) \
            .filter(Design.DataSetID == DataSet.ID) \
            .filter(DGEmodel.ContrastID == Contrast.ID) \
            .filter(DataSet.ID == self.ID).all()


class MicroArrayDataSet(DataSet):
    __tablename__ = 'MicroArrayDataSet'

    NormalizationMethod = Column("MicroArrayNormalizationMethod", Enum(MicroArrayType))

    __mapper_args__ = {
        'polymorphic_identity': ExprsType.MICRO_ARRAY
    }


class RNASeqDataSet(DataSet):
    __tablename__ = 'RNASeqDataSet'

    NormalizationMethod = Column("RNASeqNormalizationMethod", Enum(RNASeqType))

    __mapper_args__ = {
        'polymorphic_identity': ExprsType.RNA_SEQ
    }


class FeatureMapping(db.Model):
    __tablename__ = 'FeatureMapping'

    Name = Column(String(DEFAULT_STR_SIZE), nullable=False)
    FeatureIndex = Column(Integer, nullable=False, primary_key=True)
    DataSetID = Column(Integer, ForeignKey(DataSet.ID, ondelete="CASCADE"), nullable=False, primary_key=True)
    RogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex))
    OriRogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex))
    OriTaxID = Column(Integer)
    Description = Column(String(STR_DESC_SIZE))

    DataSet = relationship("DataSet", foreign_keys=[DataSetID])
    Gene = relationship("GeneAnnotation", foreign_keys=[RogerGeneIndex])
    OriGene = relationship("GeneAnnotation", foreign_keys=[OriRogerGeneIndex])

    __table_args__ = (
        UniqueConstraint(DataSetID, Name, name='FeatureName'),
        {'mysql_engine': 'InnoDB'}
    )

    def __repr__(self):
        return "<FeatureMapping(FeatureIndex='%s', DataSetID='%s', RogerGeneIndex='%s', Name='%s', " \
               "FeatureDescription='%s')>" \
               % (self.FeatureIndex, self.DataSetID, self.RogerGeneIndex, self.Name, self.Description)


class Design(db.Model):
    __tablename__ = 'Design'

    ID = Column(Integer, primary_key=True)
    DataSetID = Column(Integer, ForeignKey(DataSet.ID), nullable=False)
    # Number of variables in feature matrix
    VariableCount = Column(Integer, nullable=False)
    Name = Column(String(DEFAULT_STR_SIZE), nullable=False)
    Description = Column(String(STR_DESC_SIZE))
    # Matrix (array of array) + derived-flag
    DesignMatrix = Column(RogerJSON, nullable=False)
    # Grouping of the samples, array of strings whose number of elements must be equal with the number of samples
    SampleGroups = Column(RogerJSON, nullable=False)
    # List of existing groups / group levels
    SampleGroupLevels = Column(RogerJSON, nullable=False)
    CreatedBy = Column(String(DEFAULT_STR_SIZE), nullable=False)
    # A flag that tells the user that no human entity has locked into the design
    # if NULL, the design was not reviewed by a user
    LastReviewedBy = Column(String(DEFAULT_STR_SIZE))
    CreationTime = Column(DateTime, nullable=False)

    DataSet = relationship("DataSet", foreign_keys=[DataSetID])

    __table_args__ = (
        UniqueConstraint(DataSetID, Name, name='DesignName'),
        {'mysql_engine': 'InnoDB'}
    )

    def __repr__(self):
        return "<Design(ID='%s', DataSetID='%s', Name='%s', SampleGroups='%s', SampleGroupLevels='%s')>" \
               % (self.ID, self.DataSetID, self.Name, self.SampleGroups, self.SampleGroupLevels)

    @hybrid_property
    def design_matrix(self):
        df = DataFrame()
        for row in self.DesignMatrix:
            df[row["columnName"]] = row["values"]
        return df


class SampleSubset(db.Model):
    __tablename__ = 'SampleSubset'

    SampleIndex = Column(Integer, nullable=False, primary_key=True)
    DesignID = Column(Integer, ForeignKey(Design.ID, ondelete="CASCADE"), primary_key=True)
    IsUsed = Column(Boolean, nullable=False)
    Description = Column(String(STR_DESC_SIZE))

    Design = relationship("Design", foreign_keys=[DesignID])

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<SampleSubset(SampleIndex='%s', DesignID='%s', IsUsed='%s', Description='%s')>" \
               % (self.SampleIndex, self.DesignID, self.IsUsed, self.Description)


# TODO: Don't model it as explicit python type
class OptimalDesign(db.Model):
    __tablename__ = 'OptimalDesign'

    DataSetID = Column(Integer, ForeignKey(DataSet.ID), primary_key=True)
    DesignID = Column(Integer, ForeignKey(Design.ID, ondelete="CASCADE"), primary_key=True)

    DataSet = relationship("DataSet", foreign_keys=[DataSetID])
    Design = relationship("Design", foreign_keys=[DesignID])

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<OptimalDesign(DataSetID='%s', DesignID='%s')>" \
               % (self.DataSetID, self.DesignID)


class Contrast(db.Model):
    __tablename__ = 'Contrast'

    ID = Column(Integer, primary_key=True)
    DesignID = Column(Integer, ForeignKey(Design.ID), nullable=False)
    Name = Column(String(DEFAULT_STR_SIZE), nullable=False)
    Description = Column(String(STR_DESC_SIZE))
    CreatedBy = Column(String(DEFAULT_STR_SIZE), nullable=False)
    CreationTime = Column(DateTime, nullable=False)

    Design = relationship("Design", foreign_keys=[DesignID])

    __table_args__ = (
        UniqueConstraint(DesignID, Name, name='ContrastName'),
        {'mysql_engine': 'InnoDB'}
    )

    def __repr__(self):
        return "<ContrastColumn(ID='%s', DesignID='%s', Name='%s', Description='%s')>" \
               % (self.ID, self.DesignID, self.Name, self.Description)

    @hybrid_property
    def contrast_columns(self):
        return roger.util.as_data_frame(ContrastColumn.query
                                        .filter(ContrastColumn.ContrastID == self.ID)
                                        .order_by(ContrastColumn.ID))

    @hybrid_property
    def contrast_matrix(self):
        df = DataFrame()
        for index, row in self.contrast_columns.iterrows():
            df[row.Name] = row.ColumnData
        df.index = self.Design.design_matrix.columns
        return df


class ContrastColumn(db.Model):
    __tablename__ = 'ContrastColumn'

    ID = Column(Integer, primary_key=True)
    ContrastID = Column(Integer, ForeignKey(Contrast.ID, ondelete="CASCADE"), nullable=False)
    Name = Column(String(DEFAULT_STR_SIZE), nullable=False)
    Description = Column(String(STR_DESC_SIZE))
    #  Numeric array - numerical combination of variables in design matrix
    ColumnData = Column(RogerJSON, nullable=False)

    Contrast = relationship("Contrast", foreign_keys=[ContrastID])

    __table_args__ = (
        UniqueConstraint(ContrastID, Name, name='ContrastColumnName'),
        {'mysql_engine': 'InnoDB'}
    )

    def __repr__(self):
        return "<ContrastColumn(ID='%s', ContrastID='%s', Name='%s', ColumnData='%s')>" \
               % (self.ID, self.ContrastID, self.Name, self.ColumnData)


class DGEmethod(db.Model):
    __tablename__ = 'DGEmethod'

    ID = Column(Integer, primary_key=True)
    Name = Column(String(DEFAULT_STR_SIZE), nullable=False, unique=True)
    Description = Column(String(STR_DESC_SIZE))

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<DGEmethod(ID='%s', Name='%s', Description='%s')>" \
               % (self.ID, self.Name, self.Description)


class DGEmodel(db.Model):
    __tablename__ = 'DGEmodel'

    ContrastID = Column(Integer, ForeignKey(Contrast.ID), primary_key=True)
    DGEmethodID = Column(Integer, ForeignKey(DGEmethod.ID), primary_key=True)
    # Link to external files in study-centric working directory
    # Untrained model
    InputObjFile = Column(String(DEFAULT_STR_SIZE), nullable=False)
    # Evaluated model
    FitObjFile = Column(String(DEFAULT_STR_SIZE), nullable=False)
    MethodDescription = Column(String(STR_DESC_SIZE), nullable=False)

    Contrast = relationship("Contrast", foreign_keys=[ContrastID])
    Method = relationship("DGEmethod", foreign_keys=[DGEmethodID])

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<DGEmodel(ContrastID='%s', DGEmethodID='%s')>" \
               % (self.ContrastID, self.DGEmethodID)


class FeatureSubset(db.Model):
    __tablename__ = 'FeatureSubset'

    ID = Column(Integer, primary_key=True)
    FeatureIndex = Column(Integer, nullable=False)
    DataSetID = Column(Integer, nullable=False)
    ContrastID = Column(Integer, nullable=False)
    DGEmethodID = Column(Integer, nullable=False)
    IsUsed = Column(Boolean, nullable=False)
    Description = Column(String(STR_DESC_SIZE))

    __table_args__ = (
        ForeignKeyConstraint((FeatureIndex, DataSetID), [FeatureMapping.FeatureIndex, FeatureMapping.DataSetID]),
        ForeignKeyConstraint((ContrastID, DGEmethodID), [DGEmodel.ContrastID, DGEmodel.DGEmethodID],
                             ondelete="CASCADE"),
        {'mysql_engine': 'InnoDB'}
    )

    FeatureMapping = relationship("FeatureMapping", foreign_keys=[FeatureIndex, DataSetID])
    Model = relationship("DGEmodel", foreign_keys=[ContrastID, DGEmethodID])

    def __repr__(self):
        return "<FeatureSubset(FeatureIndex='%s', DGEmethodID='%s', IsUsed='%s', Description='%s')>" \
               % (self.FeatureIndex, self.DGEmethodID, self.IsUsed, self.Description)


class DGEtable(db.Model):
    __tablename__ = 'DGEtable'

    ContrastColumnID = Column(Integer, ForeignKey(ContrastColumn.ID), primary_key=True)
    FeatureIndex = Column(Integer, nullable=False, primary_key=True)
    DataSetID = Column(Integer, nullable=False, primary_key=True)
    ContrastID = Column(Integer, nullable=False, primary_key=True)
    DGEmethodID = Column(Integer, nullable=False, primary_key=True)
    AveExprs = Column(Float, nullable=False)
    Statistic = Column(Float, nullable=False)
    LogFC = Column(Float, nullable=False)
    PValue = Column(Float, nullable=False)
    FDR = Column(Float, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint((FeatureIndex, DataSetID), [FeatureMapping.FeatureIndex, FeatureMapping.DataSetID]),
        ForeignKeyConstraint((ContrastID, DGEmethodID), [DGEmodel.ContrastID, DGEmodel.DGEmethodID],
                             ondelete="CASCADE"),
        {'mysql_engine': 'InnoDB'}
    )

    ContrastColumn = relationship("ContrastColumn", foreign_keys=[ContrastColumnID])
    FeatureMapping = relationship("FeatureMapping", foreign_keys=[FeatureIndex, DataSetID])
    Model = relationship("DGEmodel", foreign_keys=[ContrastID, DGEmethodID])

    def __repr__(self):
        return "<DGEtable(ContrastColumnID='%s', FeatureIndex='%s', AveExprs='%s', Statistic='%s'," \
               "LogFC='%s', PValue='%s', FDR='%s')>" \
               % (self.ContrastColumnID, self.FeatureIndex, self.AveExprs,
                  self.Statistic, self.LogFC, self.PValue, self.FDR)


class GSEmethod(db.Model):
    __tablename__ = 'GSEmethod'

    ID = Column(Integer, primary_key=True)
    DGEmethodID = Column(Integer, ForeignKey(DGEmethod.ID))
    Name = Column(String(DEFAULT_STR_SIZE), nullable=False)
    Description = Column(String(STR_DESC_SIZE))

    __table_args__ = (
        UniqueConstraint(DGEmethodID, Name, name='GSEmethodPerDGE'),
        {'mysql_engine': 'InnoDB'}
    )

    DGEMethod = relationship("DGEmethod", foreign_keys=[DGEmethodID])

    def __repr__(self):
        return "<GSEmethod(ID='%s', DGEmethodID'%s' Name='%s', Description='%s')>" \
               % (self.ID, self.DGEmethodID, self.Name, self.Description)


class GSEtable(db.Model):
    __tablename__ = 'GSEtable'

    ContrastColumnID = Column(Integer, ForeignKey(ContrastColumn.ID), primary_key=True)
    GSEmethodID = Column(Integer, ForeignKey(GSEmethod.ID), primary_key=True)
    GeneSetID = Column(Integer, ForeignKey(GeneSet.ID), primary_key=True)
    Correlation = Column(Float)
    Direction = Column(Integer, nullable=False)
    PValue = Column(Float, nullable=False)
    FDR = Column(Float, nullable=False)
    EnrichmentScore = Column(Float, nullable=False)
    EffGeneCount = Column(Integer, nullable=False)

    ContrastColumn = relationship("ContrastColumn", foreign_keys=[ContrastColumnID])
    Method = relationship("GSEmethod", foreign_keys=[GSEmethodID])
    GeneSet = relationship("GeneSet", foreign_keys=[GeneSetID])

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __repr__(self):
        return "<GSEtable(ContrastColumnID='%s', GSEmethodID='%s', GeneSetID='%s', Correlation='%s'," \
               "Direction='%s', PValue='%s', FDR='%s', EnrichmentScore='%s', EffGeneCount='%s')>" \
               % (self.ContrastColumnID, self.GSEmethodID, self.GeneSetID, self.Correlation, self.Direction,
                  self.PValue, self.FDR, self.EnrichmentScore, self.EffGeneCount)
