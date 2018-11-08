import React from 'react';
import PropTypes from 'prop-types';
import {withStyles} from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Typography from '@material-ui/core/Typography';
import StudyDrawer from "Roger/components/study/study_drawer";
import ExpressionPCAPlot from "Roger/components/study/plots/expression_pca";

const styles = {
    card: {
        minWidth: 275,
        marginBottom: 12,
    },
};

function DGEView(props) {
    const {classes, study, studyAnnotation, design, contrast, dgeResult, studyBaseURL} = props;

    return (
        <StudyDrawer study={study} basePath={studyBaseURL}>
            <Card className={classes.card}>
                <CardContent>
                    <Typography variant="h5" component="h2">
                        TODO DGE
                    </Typography>
                    <ExpressionPCAPlot studyName={study.Name}
                                       designName={design.Name}
                                       contrastName={contrast.Name}
                                       dgeMethodName={dgeResult.MethodName}/>
                </CardContent>
            </Card>
        </StudyDrawer>
    );
}

DGEView.propTypes = {
    classes: PropTypes.object.isRequired,
    study: PropTypes.object.isRequired,
    design: PropTypes.object.isRequired,
    dgeResult: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
    studyBaseURL: PropTypes.string.isRequired
};

export default withStyles(styles)(DGEView);