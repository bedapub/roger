from sqlalchemy import Column, Integer, String, Boolean, REAL, DateTime, BLOB
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Model = declarative_base()


class GeneAnnotation(Model):
    __tablename__ = 'GeneAnnotation'

    RogerGeneIndex = Column(Integer, primary_key=True)
    # TODO: Version flushing not easy, need to make
    # Option 1) Make an entire Version Mapping
    # Option 2) Make an incremental invalidation of changed / removed genes
    Version = Column(String, nullable=False)
    TaxID = Column(Integer, nullable=False)
    # ALWAYS means stable Ensembl gene ID without version (.x)
    EnsemblGeneID = Column(String)
    # NCBI Gene ID
    EntrezGeneID = Column(Integer)
    GeneType = Column(String)
    GeneSymbol = Column(String, index=True)
    IsObsolete = Column(Boolean, nullable=False)

    def __repr__(self):
        return "<GeneAnnotation(RogerGeneIndex='%s', Version='%s', TaxID='%s', EnsemblGeneID='%s', EntrezGeneID='%s'," \
               " GeneSymbol='%s', IsObsolete='%s')>" \
               % (self.RogerGeneIndex, self.Version, self.TaxID,
                  self.EnsemblGeneID, self.EntrezGeneID, self.GeneSymbol, self.IsObsolete)


# TODO How to model joins?
class Ortholog(Model):
    __tablename__ = 'Ortholog'

    RogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex), primary_key=True)
    HumanRogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex), primary_key=True)

    Gene = relationship("GeneAnnotation", foreign_keys="[Ortholog.HumanRogerGeneIndex]")

    def __repr__(self):
        return "<Ortholog(RogerGeneIndex='%s', HumanRogerGeneIndex='%s')>" \
               % (self.RogerGeneIndex, self.HumanRogerGeneIndex)


class GeneSetCategory(Model):
    __tablename__ = 'GeneSetCategory'

    ID = Column(Integer, primary_key=True)
    Name = Column(String, unique=True, nullable=False)

    GeneSets = relationship("GeneSet", cascade="all, delete-orphan", back_populates="Category")

    def __repr__(self):
        return "<GeneSetCategory(ID='%s', Name='%s')>" \
               % (self.ID, self.Name)


class GeneSet(Model):
    __tablename__ = 'GeneSet'

    ID = Column(Integer, primary_key=True)
    CategoryID = Column(String, ForeignKey(GeneSetCategory.ID), nullable=False)
    Name = Column(String, nullable=False)
    # Behaviour: If TaxID == HumanTaxID then use RogerGeneIndex from this GeneSet. Else convert to human GeneSets first
    TaxID = Column(Integer, nullable=False)
    Description = Column(String)
    GeneCount = Column(Integer, nullable=False)
    # True if geneset is supposed to be internal
    IsPrivate = Column(Boolean, nullable=False)
    # Can point to reference geneset Information (e.g. in MongoDB)
    URL = Column(String)

    Category = relationship("GeneSetCategory", back_populates="GeneSets")
    Genes = relationship("GeneSetGene", cascade="all, delete-orphan", back_populates="GeneSet")

    __table_args__ = (
        UniqueConstraint(CategoryID, Name, name='GeneSetName'),
    )

    def __repr__(self):
        return "<GeneSet(ID='%s', CategoryID='%s', Name='%s', TaxID='%s', Description='%s', GeneCount='%s'," \
               "IsPrivate='%s', URL='%s')>" \
               % (self.ID, self.CategoryID, self.Name, self.TaxID, self.Description,
                  self.GeneCount, self.IsPrivate, self.URL)


# TODO: make this a regular table object, not a full-blown class
class GeneSetGene(Model):
    __tablename__ = 'GeneSetGene'

    GeneSetID = Column(Integer, ForeignKey(GeneSet.ID), primary_key=True)
    RogerGeneIndex = Column(String, ForeignKey(GeneAnnotation.RogerGeneIndex), primary_key=True)
    # TODO: Can be computed on the fly by the same mechanism as in Genesets.TaxID, but requires one less JOIN
    # HumanRogerGeneIndex = Column(String, ForeignKey(GeneAnnotation.RogerGeneIndex), primary_key=True)

    GeneSet = relationship("GeneSet", back_populates="Genes")
    Gene = relationship("GeneAnnotation", foreign_keys=[RogerGeneIndex])

    def __repr__(self):
        return "<GeneSetGene(GeneSetID='%s', RogerGeneIndex='%s')>" \
               % (self.GeneSetID, self.RogerGeneIndex)


class DataSet(Model):
    __tablename__ = 'DataSet'

    ID = Column(Integer, primary_key=True)
    Name = Column(String, unique=True, nullable=False)
    # To ensure that analysis is reproducible when loading new gene annotations into database
    GeneAnnotationVersion = Column(String, nullable=False)
    Description = Column(String)
    FeatureCount = Column(Integer, nullable=False)
    SampleCount = Column(Integer, nullable=False)
    # Path to working copy of GCT file
    ExprsWC = Column(String)
    # Path to external / save copy of GCT file
    ExprsSrc = Column(String, nullable=False)
    # Path to working copy of R Matrix from GCT file
    NormalizedExprsWC = Column(String)
    # Path to external / save copy of R Matrix from GCT file
    NormalizedExprsSrc = Column(String, nullable=False)
    ExprsType = Column(String, nullable=False)
    # Path to working copy of TDF file
    PhenoWC = Column(String)
    # Path to external / save copy of TDF file
    # TODO: TEXT or BLOB - BLOB makes levels-handling easier / Alternative: Develop own format:
    #      #1 Header + 2 extra lines about #2 type and #3 levels
    # TODO: Check if JSON is a better format
    PhenoSrc = Column(String, nullable=False)
    FeatureType = Column(String, nullable=False)
    TaxID = Column(Integer, nullable=False)
    Xref = Column(String, nullable=False)
    # External URL to (e.g. MongoDB)
    URL = Column(String, nullable=False)
    CreatedBy = Column(String, nullable=False)
    CreationTime = Column(DateTime, nullable=False)

    def __repr__(self):
        return "<DataSet(ID='%s', Name='%s')>" \
               % (self.ID, self.Name)


class FeatureMapping(Model):
    __tablename__ = 'FeatureMapping'

    FeatureIndex = Column(Integer, primary_key=True)
    DataSetID = Column(Integer, ForeignKey(DataSet.ID), primary_key=True)
    RogerGeneIndex = Column(Integer, ForeignKey(GeneAnnotation.RogerGeneIndex), primary_key=True)
    Name = Column(String, nullable=False)
    Description = Column(String)

    DataSet = relationship("DataSet", foreign_keys=[DataSetID])
    Gene = relationship("GeneAnnotation", foreign_keys=[RogerGeneIndex])

    __table_args__ = (
        UniqueConstraint(DataSetID, Name, name='FeatureName'),
    )

    def __repr__(self):
        return "<FeatureMapping(FeatureIndex='%s', DataSetID='%s', RogerGeneIndex='%s', Name='%s', " \
               "FeatureDescription='%s')>" \
               % (self.FeatureIndex, self.DataSetID, self.RogerGeneIndex, self.Name, self.Description)


class Design(Model):
    __tablename__ = 'Design'

    ID = Column(Integer, primary_key=True)
    DataSetID = Column(Integer, ForeignKey(DataSet.ID), nullable=False)
    # Number of variables in feature matrix
    VariableCount = Column(Integer, nullable=False)
    Name = Column(String, nullable=False)
    Description = Column(String)
    # TODO: Check real BLOB sizes & also consider JSON
    # R logic vector
    SampleSubset = Column(BLOB, nullable=False)
    # R logic vector
    FeatureSubset = Column(BLOB, nullable=False)
    # R Matrix
    DesignMatrix = Column(BLOB, nullable=False)
    CreatedBy = Column(String, nullable=False)
    # A flag that tells the user that no human entity has locked into the design
    # if NULL, the design was not reviewed by a user
    LastReviewedBy = Column(String)
    CreationTime = Column(String, nullable=False)

    DataSet = relationship("DataSet", foreign_keys=[DataSetID])

    __table_args__ = (
        UniqueConstraint(DataSetID, Name, name='FeatureName'),
    )

    def __repr__(self):
        return "<GeneSetCategory(ID='%s', DataSetID='%s', Name='%s')>" \
               % (self.ID, self.DataSetID, self.Name)


# TODO: Don't model it as explicit python type
class OptimalDesign(Model):
    __tablename__ = 'OptimalDesign'

    DataSetID = Column(Integer, ForeignKey(DataSet.ID), primary_key=True)
    DesignID = Column(Integer, ForeignKey(Design.ID), primary_key=True)

    DataSet = relationship("DataSet", foreign_keys=[DataSetID])
    Design = relationship("Design", foreign_keys=[DesignID])

    def __repr__(self):
        return "<OptimalDesign(DataSetID='%s', DesignID='%s')>" \
               % (self.DataSetID, self.DesignID)


class Contrast(Model):
    __tablename__ = 'Contrast'

    ID = Column(Integer, primary_key=True)
    DesignID = Column(Integer, ForeignKey(Design.ID), nullable=False)
    Name = Column(String, nullable=False)
    Description = Column(String)
    #  R numeric vector - numerical combination of variables in design matrix
    Contrast = Column(String, nullable=False)
    CreatedBy = Column(String, nullable=False)
    CreationTime = Column(DateTime, nullable=False)

    Design = relationship("Design", foreign_keys=[DesignID])

    __table_args__ = (
        UniqueConstraint(DesignID, Name, name='ContrastName'),
    )

    def __repr__(self):
        return "<Contrast(ID='%s', DesignID='%s', Name='%s')>" \
               % (self.ID, self.DesignID, self.Name)


class DGEmethod(Model):
    __tablename__ = 'DGEmethod'

    ID = Column(Integer, primary_key=True)
    Name = Column(String, nullable=False, unique=True)
    Description = Column(String)
    Version = Column(String, nullable=False)

    def __repr__(self):
        return "<DGEmethod(ID='%s', Name='%s', Description='%s', Version='%s')>" \
               % (self.ID, self.Name, self.Description, self.Version)


class DGEmodel(Model):
    __tablename__ = 'DGEmodel'

    DesignID = Column(Integer, ForeignKey(Design.ID), primary_key=True)
    DGEmethodID = Column(Integer, ForeignKey(DGEmethod.ID), primary_key=True)
    # Link to external files in study-centric working directory
    # Untrained model TODO store in R binary file
    InputObjFile = Column(String, nullable=False)
    # Evaluated model TODO store in R binary file
    FitObjFile = Column(String, nullable=False)

    Design = relationship("Design", foreign_keys=[DesignID])
    Method = relationship("DGEmethod", foreign_keys=[DGEmethodID])

    def __repr__(self):
        return "<DGEmodel(DesignID='%s', DGEmethodID='%s')>" \
               % (self.DesignID, self.DGEmethodID)


class DGEtable(Model):
    __tablename__ = 'DGEtable'

    ContrastID = Column(Integer, ForeignKey(Contrast.ID), primary_key=True)
    FeatureIndex = Column(Integer, ForeignKey(FeatureMapping.FeatureIndex), primary_key=True)
    AveExprs = Column(REAL, nullable=False)
    Statistic = Column(REAL, nullable=False)
    LogFC = Column(REAL, nullable=False)
    PValue = Column(REAL, nullable=False)
    FDR = Column(REAL, nullable=False)

    Contrast = relationship("Contrast", foreign_keys=[ContrastID])
    FeatureMapping = relationship("FeatureMapping", foreign_keys=[FeatureIndex])

    def __repr__(self):
        return "<DGEtable(ContrastID='%s', FeatureIndex='%s', AveExprs='%s', Statistic='%s'," \
               "LogFC='%s', PValue='%s', FDR='%s')>" \
               % (self.ContrastID, self.FeatureIndex, self.AveExprs, self.Statistic, self.LogFC, self.PValue, self.FDR)


class GSEmethod(Model):
    __tablename__ = 'GSEmethod'

    ID = Column(Integer, primary_key=True)
    Name = Column(String, nullable=False, unique=True)
    Description = Column(String)
    Version = Column(String, nullable=False)

    def __repr__(self):
        return "<GSEmethod(ID='%s', Name='%s', Description='%s', Version='%s')>" \
               % (self.ID, self.Name, self.Description, self.Version)


class GSEtable(Model):
    __tablename__ = 'GSEtable'

    ContrastID = Column(Integer, ForeignKey(Contrast.ID), primary_key=True)
    GSEmethodID = Column(Integer, ForeignKey(GSEmethod.ID), primary_key=True)
    GeneSetID = Column(Integer, ForeignKey(GeneSet.ID), primary_key=True)
    Correlation = Column(REAL, nullable=False)
    Direction = Column(Integer, nullable=False)
    PValue = Column(REAL, nullable=False)
    FDR = Column(REAL, nullable=False)
    EnrichmentScore = Column(REAL, nullable=False)
    EffGeneCount = Column(Integer, nullable=False)

    Contrast = relationship("Contrast", foreign_keys=[ContrastID])
    Method = relationship("GSEmethod", foreign_keys=[GSEmethodID])
    GeneSet = relationship("GeneSet", foreign_keys=[GeneSetID])

    def __repr__(self):
        return "<GSEtable(ContrastID='%s', GSEmethodID='%s', GeneSetID='%s', Correlation='%s'," \
               "Direction='%s', PValue='%s', FDR='%s', EnrichmentScore='%s', EffGeneCount='%s')>" \
               % (self.ContrastID, self.GSEmethodID, self.GeneSetID, self.Correlation, self.Direction, self.PValue,
                  self.FDR, self.EnrichmentScore, self.EffGeneCount)
