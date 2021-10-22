import React, {useEffect, useState} from "react";
import Style from "./Homepage.module.css";
import {
    Anchor,
    Box,
    Button,
    Chapter,
    Field,
    Footer,
    Form,
    Heading,
    LayoutFill,
    Panel,
    Table
} from "@steffo/bluelib-react";
import {useAppContext} from "../../libs/Context";
import schema from "../config";
import {Link, useHistory} from "react-router-dom";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";


export default function Dashboard(props) {
    const {instanceIp, setInstanceIp} = useAppContext()
    const {connected, setConnected} = useAppContext()
    const {token, setToken} = useAppContext()
    const {instance, setInstance} = useAppContext()
    const {user, setUser} = useAppContext()

    const history = useHistory()

    function disconnect() {
        setUser(null)
        setToken(null)
        history.push("/srv/" + instanceIp)
    }

    useEffect(() => {
        if (!instanceIp || !token) {
            setConnected(false)
            history.push("/srv/" + instanceIp)
        }
    }, [token])

    if(user){
    return (
        <div>
            <div className={Style.Home}>
                <div className={Style.lander}>
                    <Heading level={2}>Benvenuto, {user.surname}</Heading>
                    <Button onClick={event => {
                        disconnect()
                    }}> Disconnettiti </Button>
                </div>
            </div>
        </div>
    );}
    else return(<div/>)
}