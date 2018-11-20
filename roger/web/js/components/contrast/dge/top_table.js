import React from 'react';
import PropTypes from 'prop-types';
import Input from '@material-ui/core/Input';
import CircularProgress from '@material-ui/core/CircularProgress';
import {withStyles} from '@material-ui/core/styles';
import {IntegratedFiltering} from '@devexpress/dx-react-grid';
import {IntegratedPaging} from '@devexpress/dx-react-grid';
import {IntegratedSelection} from '@devexpress/dx-react-grid';
import {IntegratedSorting} from '@devexpress/dx-react-grid';
import {PagingState} from '@devexpress/dx-react-grid';
import {SelectionState} from '@devexpress/dx-react-grid';
import {SortingState} from '@devexpress/dx-react-grid';
import {DataTypeProvider} from '@devexpress/dx-react-grid';

import {DragDropProvider} from '@devexpress/dx-react-grid-material-ui';
import {Grid} from '@devexpress/dx-react-grid-material-ui';
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
});


const getColor = (amount) => {
    if (amount > 0.1) {
        return '#F44336';
    }
    if (amount > 0.05) {
        return '#FFC107';
    }

    return '#009688';
};

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
        <span className={classes.numericValue} style={{color: getColor(value)}}>{value}</span>
);


class TopTable extends React.Component {

    constructor(props) {
        super(props);
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
            loading: true,
        };
    }

    componentDidMount() {
        fetch(`${URL_PREFIX}/study/${this.props.studyName}`
            + `/design/${this.props.designName}`
            + `/contrast/${this.props.contrastName}`
            + `/dge/${this.props.dgeMethodName}/tbl/json`)
            .then(result => result.json())
            .then(dge_tbl => {
                console.log(dge_tbl);
                this.setState({loading: false, rows: dge_tbl.data});
            });
    }

    render() {
        const {
            rows, columns, pageSizes,
            numericColumns, loading
        } = this.state;

        return (
            <div>
                <Grid rows={rows} columns={columns}>
                    <SortingState
                        defaultSorting={[
                            {columnName: 'LogFC', direction: 'asc'},
                        ]}
                    />

                    <FilteringState/>
                    <SelectionState/>
                    <PagingState/>

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