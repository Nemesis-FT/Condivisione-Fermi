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


export default function Register(props) {
    const {instanceIp, setInstanceIp} = useAppContext()
    const {connected, setConnected} = useAppContext()
    const {token, setToken} = useAppContext()
    const [name, setName] = useState("")
    const [surname, setSurname] = useState("")
    const [className, setClassName] = useState("")
    const [email, setEmail] = useState("")
    const [parentEmail, setParentEmail] = useState("")
    const [password, setPassword] = useState("")
    const [passwordConfirm, setPasswordConfirm] = useState("")
    let history = useHistory();
    let { t } = useTranslation()

    useEffect(() => {
        if (!instanceIp) {
            setConnected(false)
            history.push("/")
        }
    })

    async function register() {
        const response = await fetch(schema + instanceIp + "/users/", {
            method: "POST",
            credentials: "include",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': process.env.DOMAIN
            },
            body: JSON.stringify({
                "name": name,
                "surname": surname,
                "email": email,
                "parent_email": parentEmail,
                "class_number": className,
                "type": 0,
                "password": password
            })
        });
        if (response.status === 200) {
            let values = await response.json()
            console.debug(values)
            alert("Registrazione completata!")
        }
    }

    return (
        <div>
            <Box>
                <Dialog>
                    {t("login_page.legal_notice")}
                </Dialog>
                <Form>
                    <Form.Row>
                        <Form.Field onSimpleChange={e => setName(e)} value={name} required={true}
                                    placeholder={t("login_page.labels.name")}>
                        </Form.Field>
                        <Form.Field onSimpleChange={e => setSurname(e)} value={surname} required={true}
                                    placeholder={t("login_page.labels.surname")}>
                        </Form.Field>
                        <Form.Field onSimpleChange={e => setClassName(e)} value={className} required={true}
                                    placeholder={t("login_page.labels.class_name")}>
                        </Form.Field>
                    </Form.Row>
                    <Form.Row>
                        <Form.Field onSimpleChange={e => setEmail(e)} value={email}
                                    required={true}
                                    placeholder={t("login_page.labels.personal_email")}>
                        </Form.Field>
                        <Form.Field onSimpleChange={e => setParentEmail(e)} value={parentEmail}
                                    required={true}
                                    placeholder={t("login_page.labels.parent_email")}>
                        </Form.Field>
                    </Form.Row>
                    <Form.Row>
                        <Form.Field type="password" onSimpleChange={e => setPassword(e)} value={password}
                                    required={true}
                                    placeholder={t("login_page.labels.password")}>
                        </Form.Field>
                        <Form.Field type="password" onSimpleChange={e => setPasswordConfirm(e)} value={passwordConfirm}
                                    required={true}
                                    placeholder={t("login_page.labels.confirm_password")}>
                        </Form.Field>
                    </Form.Row>
                </Form>
                <Form.Row>
                    <Button children={t("login_page.register_button")} onClick={e => register()}/>
                </Form.Row>
            </Box>
        </div>
    );
}