import React from 'react';
import PropTypes from 'prop-types';
import {withStyles} from '@material-ui/core/styles';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Grid from '@material-ui/core/Grid';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Typography from '@material-ui/core/Typography';


import StudyDrawer from "Roger/components/study/study_drawer";
import DesignTable from "Roger/components/design/design_table";

const styles = {
    card: {
        minWidth: 275,
        marginBottom: 12,
    },
};

function countSampleSubset(sampleSubset) {
    return sampleSubset.filter(entry => entry.IsUsed).length
}

function DesignOverview(props) {
    const {classes, study, design, sampleAnnotation, basePath} = props;

    return (
        <StudyDrawer study={study} basePath={basePath}>
            <Card className={classes.card}>
                <CardContent>
                    <Typography variant="h5" component="h2">
                        About the Study
                    </Typography>
                    <Grid container spacing={24}>
                        <Grid item xs={6}>
                            <List>
                                <ListItem>
                                    <ListItemText primary="Description" secondary={design.Description}/>
                                </ListItem>
                                <ListItem>
                                    <ListItemText primary="Variable Count" secondary={design.VariableCount}/>
                                </ListItem>
                                <ListItem>
                                    <ListItemText primary="Used Samples"
                                                  secondary={`${countSampleSubset(design.SampleSubset)} `
                                                  + ` of ${study.SampleCount}`}/>
                                </ListItem>
                            </List>
                        </Grid>
                        <Grid item xs={6}>
                            <List>
                                <ListItem>
                                    <ListItemText primary="Last Reviewed by" secondary={design.LastReviewedBy}/>
                                </ListItem>
                                <ListItem>
                                    <ListItemText primary="Created by"
                                                  secondary={design.CreatedBy}/>
                                </ListItem>
                            </List>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>
            <DesignTable
                design={design}
                sampleAnnotation={sampleAnnotation}/>
        </StudyDrawer>
    );
}

DesignOverview.propTypes = {
    classes: PropTypes.object.isRequired,
    design: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
    basePath: PropTypes.string.isRequired
};

export default withStyles(styles)(DesignOverview);