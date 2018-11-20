import React from 'react';
import Plot from 'react-plotly.js';

import {URL_PREFIX} from "Roger/logic/rest";
import CircularProgress from '@material-ui/core/CircularProgress';

export default class ExpressionPCAPlot extends React.Component {
    constructor(props) {
        super(props);
        this.state = {loaded: false, renderedComp: []};
    }

    componentDidMount() {
        fetch(`${URL_PREFIX}/study/${this.props.studyName}`
            + `/design/${this.props.designName}`
            + `/contrast/${this.props.contrastName}`
            + `/dge/${this.props.dgeMethodName}/plot/pca`)
            .then(result => result.json())
            .then(pca_data => {
                let studyComp =
                    <Plot
                        data={pca_data.data}
                        layout={pca_data.layout}
                    />;
                this.setState({loaded: true, renderedComp: studyComp});
            });
    }

    render() {
        return this.state.loaded ? this.state.renderedComp : <CircularProgress />;
    }
}