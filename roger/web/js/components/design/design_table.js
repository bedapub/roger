import React from 'react';
import PropTypes from 'prop-types';
import {withStyles} from '@material-ui/core/styles';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Typography from '@material-ui/core/Typography';

const styles = {
    card: {
        minWidth: 275,
        marginBottom: 12,
    },
    table: {
        minWidth: 700,
    },
};


function DesignTable(props) {
    const {classes, design, sampleAnnotation} = props;

    return (
        <Card className={classes.card}>
            <CardContent>
                <Typography variant="h5" component="h2">
                    Design Matrix & Sample Information
                </Typography>
                <Table className={classes.table}>
                    <TableHead>
                        <TableRow>
                            <TableCell colSpan={3}>Sample Information</TableCell>
                            <TableCell colSpan={design.VariableCount}>Variables</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell numeric>Sample Group</TableCell>
                            <TableCell numeric>Used?</TableCell>
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
            </CardContent>
        </Card>
    );
}

DesignTable.propTypes = {
    classes: PropTypes.object.isRequired,
    design: PropTypes.object.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
};

export default withStyles(styles)(DesignTable);