import React from 'react';
import PropTypes from 'prop-types';
import Input from '@material-ui/core/Input';
import CircularProgress from '@material-ui/core/CircularProgress';
import Button from '@material-ui/core/Button';
import {withStyles} from '@material-ui/core/styles';
import Grid from '@material-ui/core/Grid';
import {IntegratedFiltering} from '@devexpress/dx-react-grid';
import {IntegratedPaging} from '@devexpress/dx-react-grid';
import {IntegratedSelection} from '@devexpress/dx-react-grid';
import {IntegratedSorting} from '@devexpress/dx-react-grid';
import {PagingState} from '@devexpress/dx-react-grid';
import {SelectionState} from '@devexpress/dx-react-grid';
import {SortingState} from '@devexpress/dx-react-grid';
import {DataTypeProvider} from '@devexpress/dx-react-grid';

import {DragDropProvider} from '@devexpress/dx-react-grid-material-ui';
import {Grid as DataGrid} from '@devexpress/dx-react-grid-material-ui';
import {PagingPanel} from '@devexpress/dx-react-grid-material-ui';
import {Table} from '@devexpress/dx-react-grid-material-ui';
import {TableFilterRow} from '@devexpress/dx-react-grid-material-ui';
import {TableHeaderRow} from '@devexpress/dx-react-grid-material-ui';
import {TableSelection} from '@devexpress/dx-react-grid-material-ui';
import {FilteringState} from "@devexpress/dx-react-grid/dist/dx-react-grid.umd";

import {URL_PREFIX} from "Roger/logic/rest";

const availableFilterOperations = [
    'equal', 'notEqual',
    'greaterThan', 'greaterThanOrEqual',
    'lessThan', 'lessThanOrEqual',
];

const styles = theme => ({
    numericValue: {
        fontWeight: theme.typography.fontWeightMedium,
    },
    numericInput: {
        width: '100%',
    },
    button: {
        margin: theme.spacing.unit,
    },
});


const NumericEditor = withStyles(styles)(({onValueChange, classes, value}) => {
        const handleChange = (event) => {
            const {value: targetValue} = event.target;
            if (targetValue.trim() === '') {
                onValueChange(undefined);
                return;
            }
            onValueChange(parseFloat(targetValue));
        };
        return (
            <Input
                type="number"
                classes={{
                    input: classes.numericInput,
                }}
                fullWidth={true}
                value={value}
                inputProps={{
                    min: 0,
                    placeholder: 'Filter...',
                }}
                onChange={handleChange}
            />
        );
    }
);

const NumericFormatter = withStyles(styles)(
    ({value, classes}) =>
        <span className={classes.numericValue}>{value}</span>
);


class TopTable extends React.Component {
    constructor(props) {
        super(props);
        this.dgeTableURL = `${URL_PREFIX}/study/${this.props.studyName}`
            + `/design/${this.props.designName}`
            + `/contrast/${this.props.contrastName}`
            + `/dge/${this.props.dgeMethodName}/tbl`;
        this.state = {
            columns: [
                {name: 'FeatureIndex', title: 'Feature Index'},
                {name: 'Name', title: 'Feature Name'},
                {name: 'GeneSymbol', title: 'GeneSymbol'},
                {name: 'AveExprs', title: 'AveExprs'},
                {name: 'Statistic', title: 'Statistic'},
                {name: 'LogFC', title: 'LogFC'},
                {name: 'PValue', title: 'PValue'},
                {name: 'FDR', title: 'FDR'},
            ],
            numericColumns: ['PValue', 'FDR', 'LogFC', 'AveExprs', 'Statistic'],
            pageSizes: [50, 100, 200],
            rows: [],
            selection: [],
            loading: true,
        };
        this.changeSelection = selection => {
            this.setState({
                selection,
            });
            console.log(this.state);
        }
    }

    componentDidMount() {
        fetch(`${this.dgeTableURL}/json`)
            .then(result => result.json())
            .then(dge_tbl => {
                this.setState({loading: false, rows: dge_tbl.data});
            });
    }

    render() {
        const classes = this.props;
        const {
            rows, selection, columns, pageSizes,
            numericColumns, loading
        } = this.state;

        return (
            <div>
                <DataGrid rows={rows} columns={columns}>
                    <SortingState
                        defaultSorting={[
                            {columnName: 'LogFC', direction: 'asc'},
                        ]}
                    />

                    <FilteringState/>
                    <SelectionState/>
                    <PagingState/>
                    <SelectionState
                        selection={selection}
                        onSelectionChange={this.changeSelection}/>

                    <IntegratedFiltering/>
                    <IntegratedSorting/>
                    <IntegratedPaging/>
                    <IntegratedSelection/>

                    <DataTypeProvider formatterComponent={NumericFormatter}
                                      editorComponent={NumericEditor}
                                      availableFilterOperations={availableFilterOperations}
                                      for={numericColumns}/>
                    <DragDropProvider/>


                    <Table/>
                    <TableSelection showSelectAll={true}/>

                    <TableHeaderRow showSortingControls={true}/>
                    <TableFilterRow showFilterSelector={true}/>
                    <PagingPanel pageSizes={pageSizes}/>
                </DataGrid>
                <Grid container spacing={24}>
                    <Grid item>
                        <Button variant="contained"
                                className={classes.button}
                                href={`${this.dgeTableURL}/csv`}>
                            Download All
                        </Button>
                    </Grid>
                    <Grid item>
                        <Button variant="contained"
                                className={classes.button}
                                disabled={this.state.selection.length === 0}>
                            Download Selected
                        </Button>
                    </Grid>
                </Grid>
                {loading && <CircularProgress/>}
            </div>
        );
    }
}


TopTable.propTypes = {
    classes: PropTypes.object.isRequired,
    studyName: PropTypes.string.isRequired,
    designName: PropTypes.string.isRequired,
    contrastName: PropTypes.string.isRequired,
    dgeMethodName: PropTypes.string.isRequired,
};

export default withStyles(styles)(TopTable);