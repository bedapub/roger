import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router, Route, Switch} from "react-router-dom";

import {NotFound} from "./not_found";
import {StudiesView} from "./studies";
import {SingleStudyView} from "./study";
import "isomorphic-fetch"
import 'typeface-roboto';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        };
    }

    componentDidCatch(error, info) {
        // Display fallback UI
        this.setState({hasError: true, error: error, errorInfo: info});
    }

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return (
                <div>
                    <h1>Something went wrong.</h1>
                    <details open style={{whiteSpace: 'pre-wrap'}}>
                        {this.state.error && this.state.error.toString()}
                        <br/>
                        {this.state.errorInfo.componentStack}
                    </details>
                </div>
            );
        }
        return this.props.children;
    }
}

const App = () => (
    <ErrorBoundary>
        <Router>
            <div>
                <Switch>
                    <Route exact path="/" component={StudiesView}/>
                    <Route path="/study/:study_name" component={SingleStudyView}/>
                    <Route path="/study" component={StudiesView}/>
                    <Route component={NotFound}/>
                </Switch>
            </div>
        </Router>
    </ErrorBoundary>
);

ReactDOM.render(<App/>, document.getElementById('app'));
