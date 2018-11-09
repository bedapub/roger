import React from 'react';
import Plot from 'react-plotly.js';

import {URL_PREFIX} from "Roger/logic/rest";
import './loading_spinner.css';

const SpinnerAnimation =
    <div className="lds-ring">
        <div/>
        <div/>
        <div/>
        <div/>
    </div>;

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
                let renderedComp = volcano_data.map(plotData =>
                    <Plot key={plotData.layout.title}
                        data={plotData.data}
                        layout={plotData.layout}
                    />
                );
                this.setState({loaded: true, renderedComp: renderedComp});
            });
    }

    render() {
        return this.state.loaded ? this.state.renderedComp : SpinnerAnimation;
    }
}