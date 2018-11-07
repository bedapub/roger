import React from 'react';
import PropTypes from 'prop-types';
import {withStyles} from '@material-ui/core/styles';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Card from '@material-ui/core/Card';
import Grid from '@material-ui/core/Grid';
import CardContent from '@material-ui/core/CardContent';
import Typography from '@material-ui/core/Typography';

const styles = {
    card: {
        minWidth: 275,
        marginBottom: 12,
    },
};

function StudyOverview(props) {
    const {classes, study, studyAnnotation} = props;

    return (
        <div>
            <Card className={classes.card}>
                <CardContent>
                    <Typography variant="h5" component="h2">
                        About the Study
                    </Typography>
                    <Grid container xs={12} spacing={24}>
                        <Grid item xs={6}>
                            <List>
                                <ListItem>
                                    <ListItemText primary="Description" secondary={study.Description}/>
                                </ListItem>
                                <ListItem>
                                    <ListItemText primary="Sample count" secondary={study.SampleCount}/>
                                </ListItem>
                                <ListItem>
                                    <ListItemText primary="Feature count" secondary={study.FeatureCount}/>
                                </ListItem>
                            </List>
                        </Grid>
                        <Grid item xs={6}>
                            <List>
                                <ListItem>
                                    <ListItemText primary="Expression type" secondary={study.ExpressionType}/>
                                </ListItem>
                                <ListItem>
                                    <ListItemText primary="Gene annotation version"
                                                  secondary={study.GeneAnnotationVersion}/>
                                </ListItem>
                                <ListItem>
                                    <ListItemText primary="Created by" secondary={study.CreatedBy}/>
                                </ListItem>
                            </List>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>
        </div>
    );
}

StudyOverview.propTypes = {
    classes: PropTypes.object.isRequired,
    study: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired
};

export default withStyles(styles)(StudyOverview);