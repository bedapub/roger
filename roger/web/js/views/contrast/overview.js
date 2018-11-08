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

const styles = {
    card: {
        minWidth: 275,
        marginBottom: 12,
    },
};

function ContrastOverviewView(props) {
    const {classes, study, contrast, studyBaseURL} = props;

    return (
        <StudyDrawer study={study} basePath={studyBaseURL}>
            <Card className={classes.card}>
                <CardContent>
                    <Typography variant="h5" component="h2">
                        About the contract: {contrast.Name}
                    </Typography>
                    <Grid container spacing={24}>
                        <Grid item xs={6}>
                            <List>
                                <ListItem>
                                    <ListItemText primary="Description" secondary={contrast.Description}/>
                                </ListItem>
                            </List>
                        </Grid>
                        <Grid item xs={6}>
                            <List>
                                <ListItem>
                                    <ListItemText primary="Created by" secondary={contrast.CreatedBy}/>
                                </ListItem>
                            </List>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>
        </StudyDrawer>
    );
}

ContrastOverviewView.propTypes = {
    classes: PropTypes.object.isRequired,
    study: PropTypes.object.isRequired,
    contrast: PropTypes.object.isRequired,
    studyBaseURL: PropTypes.string.isRequired
};

export default withStyles(styles)(ContrastOverviewView);