import React, {useEffect, useState} from "react";
import {
    Anchor,
    Box,
    Button,
    Chapter, Dialog,
    Field,
    Footer,
    Form,
    Heading,
    LayoutFill,
    Panel,
    Table
} from "@steffo/bluelib-react";
import {useAppContext} from "../../libs/Context";
import {Link, useHistory} from "react-router-dom";
import schema from "../config";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import {useTranslation} from "react-i18next";


export default function Login(props) {
    const {instanceIp, setInstanceIp} = useAppContext()
    const {connected, setConnected} = useAppContext()
    const {token, setToken} = useAppContext()
    const {user, setUser} = useAppContext()
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    let history = useHistory();
    const { t } = useTranslation();

    useEffect(() => {
        if (!instanceIp) {
            setConnected(false)
            history.push("/")
        }
    })

    async function login() {
        var details = {
            "grant_type": "password",
            "username": email,
            "password": password
        }
        var formB = []
        for (var property in details) {
            var encodedKey = encodeURIComponent(property);
            var encodedValue = encodeURIComponent(details[property]);
            formB.push(encodedKey + "=" + encodedValue);
        }
        formB = formB.join("&");

        const response = await fetch(schema + instanceIp + "/token", {
            method: "POST",
            credentials: "include",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'Access-Control-Allow-Origin': process.env.DOMAIN
            },
            body: formB
        });
        if (response.status === 200) {
            let values = await response.json()
            setToken(values.access_token)
            await getUserData(values.access_token)
            history.push("/dashboard")
        } else {
            alert(t("alerts.login_error"))
        }
    }

    async function getUserData(token){
        const response = await fetch(schema + instanceIp + "/users/me", {
            method: "GET",
            credentials: "include",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': "Bearer " + token,
                'Access-Control-Allow-Origin': process.env.DOMAIN
            },
        });
        if (response.status === 200) {
            let values = await response.json()
            setUser(values)
        }
    }

    return (
        <div>
            <Box>
                <Form>
                    <Form.Row>
                        <Form.Field onSimpleChange={e => setEmail(e)} value={email} required={true}
                                    placeholder={t("login_page.labels.email")}>
                        </Form.Field>
                    </Form.Row>
                    <Form.Row>
                        <Form.Field type="password" onSimpleChange={e => setPassword(e)} value={password}
                                    required={true}
                                    placeholder={t("login_page.labels.password")}>
                        </Form.Field>
                    </Form.Row>
                </Form>
                <Form.Row>
                    <Button children={t("login_page.login_button")} onClick={e => login()}/>
                </Form.Row>
            </Box>
        </div>
    );
}