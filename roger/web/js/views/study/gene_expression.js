import React from 'react';
import PropTypes from 'prop-types';
import {withStyles} from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Typography from '@material-ui/core/Typography';
import StudyDrawer from "Roger/components/study/study_drawer";

const styles = {
    card: {
        minWidth: 275,
        marginBottom: 12,
    },
};

function GeneExpressionView(props) {
    const {classes, study, studyAnnotation, basePath} = props;

    return (
        <StudyDrawer study={study} basePath={basePath}>
            <Card className={classes.card}>
                <CardContent>
                    <Typography variant="h5" component="h2">
                        TODO Gene expression
                    </Typography>
                </CardContent>
            </Card>
        </StudyDrawer>
    );
}

GeneExpressionView.propTypes = {
    classes: PropTypes.object.isRequired,
    study: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
    basePath: PropTypes.string.isRequired
};

export default withStyles(styles)(GeneExpressionView);