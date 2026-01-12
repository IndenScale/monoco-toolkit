"use client";

import {
  Navbar,
  NavbarGroup,
  NavbarHeading,
  NavbarDivider,
  Alignment,
  Button,
} from "@blueprintjs/core";
import DaemonStatus from "./DaemonStatus";

export default function AppNavbar() {
  return (
    <Navbar className="bp5-dark">
      <NavbarGroup align={Alignment.LEFT}>
        <NavbarHeading>Monoco Kanban</NavbarHeading>
        <NavbarDivider />
        <Button className="bp5-minimal" icon="home" text="Home" />
        <Button className="bp5-minimal" icon="document" text="Files" />
      </NavbarGroup>
      <NavbarGroup align={Alignment.RIGHT}>
        <DaemonStatus />
      </NavbarGroup>
    </Navbar>
  );
}
