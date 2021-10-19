import React from "react";
import {BrowserRouter, Route, Switch} from "react-router-dom";
import Home from "./containers/Home"
import Homepage from "./containers/Instance/Homepage";
import NotFound from "./containers/NotFound";
import Resume from "./containers/Resume";

export default function Routes() {
    return (
        <BrowserRouter>
            <Switch>
                <Route exact path="/">
                    <Home/>
                </Route>
                <Route exact path ="/srv" children={<Resume/>}/>
                <Route exact path ="/srv/:url" children={<Homepage/>}/>
                <Route>
                    <NotFound/>
                </Route>
            </Switch>
        </BrowserRouter>
    );
}