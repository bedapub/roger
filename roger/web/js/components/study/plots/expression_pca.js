import React from 'react';
import Plot from 'react-plotly.js';
import PropTypes from 'prop-types';
import CircularProgress from '@material-ui/core/CircularProgress';
import Select from '@material-ui/core/Select';
import MenuItem from '@material-ui/core/MenuItem';

import {URL_PREFIX} from "Roger/logic/rest";

const groupBy = function (xs, key) {
    return xs.reduce(function (rv, x) {
        (rv[x[key]] = rv[x[key]] || []).push(x);
        return rv;
    }, {});
};

export default class ExpressionPCAPlot extends React.Component {
    constructor(props) {
        super(props);
        this.state = {loaded: false, pcaData: [], groupColumns: [], currentGroupColumn: null};
        this.handleChange = event => {
            this.setState({currentGroupColumn: event.target.value});
        }
    }

    componentDidMount() {
        fetch(`${URL_PREFIX}/study/${this.props.studyName}`
            + `/design/${this.props.designName}`
            + `/contrast/${this.props.contrastName}`
            + `/dge/${this.props.dgeMethodName}/plot/pca`)
            .then(result => result.json())
            .then(pcaData => {
                const groupColumns = this.props.sampleAnnotation.schema
                    .fields.map(e => e.name);
                groupColumns.splice(groupColumns.indexOf('index'), 1);
                groupColumns.splice(groupColumns.indexOf('SAMPLE'), 1);

                this.setState({
                    loaded: true,
                    pcaData: pcaData,
                    groupColumns: groupColumns,
                    currentGroupColumn: groupColumns[0]
                });
            });
    }

    render() {
        if (this.state.loaded) {
            const pcaData = this.state.pcaData;

            const groupedAnno = groupBy(this.props.sampleAnnotation.data, this.state.currentGroupColumn);
            const groupedData = groupBy(pcaData.data, "name");

            const data = [];
            for (const key in groupedAnno) {
                if (groupedAnno.hasOwnProperty(key)) {
                    const series = {
                        "x": groupedAnno[key].map(e => groupedData[e['SAMPLE']][0]['x']),
                        "y": groupedAnno[key].map(e => groupedData[e['SAMPLE']][0]['y']),
                        "text": groupedAnno[key].map(e => groupedData[e['SAMPLE']][0]['name']),
                        "mode": 'markers',
                        "type": 'scatter',
                        "name": key
                    };
                    data.push(series)
                }
            }

            return <div style={{display: "inline-block"}}>
                <Plot
                    data={data}
                    layout={pcaData.layout}
                /> <br/>
                <Select style={{marginLeft: "120px"}} value={this.state.currentGroupColumn} name="currentGroupColumn" onChange={this.handleChange}>
                    {this.state.groupColumns.map(groupColumn =>
                        <MenuItem key={groupColumn} value={groupColumn}>{groupColumn}</MenuItem>
                    )}
                </Select>
            </div>;
        }
        return <CircularProgress/>;
    }
}

ExpressionPCAPlot.propTypes = {
    studyName: PropTypes.string.isRequired,
    sampleAnnotation: PropTypes.object.isRequired,
    designName: PropTypes.string.isRequired,
    contrastName: PropTypes.string.isRequired,
    dgeMethodName: PropTypes.string.isRequired,
};
