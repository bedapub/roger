import React from 'react';
import PropTypes from 'prop-types';
import {withStyles} from '@material-ui/core/styles';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

const styles = theme => ({
    root: {
        width: '100%',
        marginTop: theme.spacing.unit * 3,
        overflowX: 'auto',
    },
    table: {
        minWidth: 700,
    },
});


function DesignTable(props) {
    const {classes, design, sampleAnnotation} = props;

    console.log(design);
    console.log(sampleAnnotation);

    return (
        <Paper className={classes.root}>
            <Table className={classes.table}>
                <TableHead>
                    <TableRow>
                        <TableCell>Sample Group</TableCell>
                        <TableCell>Used?</TableCell>
                        <TableCell numeric>Sample Name</TableCell>
                        {design.DesignMatrix.map(col => {
                            return <TableCell key={col.columnName} numeric>
                                {col.columnName} {col.isCovariate ? <span><br/>(covariate)</span> : ""}
                            </TableCell>
                        })}
                    </TableRow>
                </TableHead>
                <TableBody>
                    {sampleAnnotation.data.map((sample, index) => {
                        return (
                            <TableRow key={sample.SAMPLE}>
                                <TableCell component="th" scope="row" numeric>
                                    {design.SampleGroups[index]}
                                </TableCell>
                                <TableCell component="th" scope="row" numeric>
                                    {design.SampleSubset[index].IsUsed ? "Yes" : "No"}
                                </TableCell>
                                <TableCell component="th" scope="row" numeric>
                                    {sample.SAMPLE}
                                </TableCell>
                                {design.DesignMatrix.map(col => {
                                    return <TableCell key={col.columnName} numeric>
                                        {col.values[index]}
                                        </TableCell>
                                })}
                            </TableRow>
                        );
                    })}
                </TableBody>
            </Table>
        </Paper>
    );
}

DesignTable.propTypes = {
    classes: PropTypes.object.isRequired,
    design: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
};

export default withStyles(styles)(DesignTable);