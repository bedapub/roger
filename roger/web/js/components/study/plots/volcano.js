import React from 'react';
import Plot from 'react-plotly.js';

import {URL_PREFIX} from "Roger/logic/rest";
import CircularProgress from '@material-ui/core/CircularProgress';

export default class DGEVolcanoPlot extends React.Component {
    constructor(props) {
        super(props);
        this.state = {loaded: false, renderedComp: []};
    }

    componentDidMount() {
        fetch(`${URL_PREFIX}/study/${this.props.studyName}`
            + `/design/${this.props.designName}`
            + `/contrast/${this.props.contrastName}`
            + `/dge/${this.props.dgeMethodName}/plot/volcano`)
            .then(result => result.json())
            .then(volcano_data => {
                let renderedComp =
                    <Plot
                        data={volcano_data.data}
                        layout={volcano_data.layout}
                    />;
                this.setState({loaded: true, renderedComp: renderedComp});
            });
    }

    render() {
        return this.state.loaded ? this.state.renderedComp : <CircularProgress />;
    }
}