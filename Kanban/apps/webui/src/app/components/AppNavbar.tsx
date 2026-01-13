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
    <Navbar className="bp6-dark">
      <NavbarGroup align={Alignment.LEFT}>
        <NavbarHeading>Monoco Kanban</NavbarHeading>
        <NavbarDivider />
        <Button variant="minimal" icon="home" text="Home" />
        <Button variant="minimal" icon="document" text="Files" />
      </NavbarGroup>
      <NavbarGroup align={Alignment.RIGHT}>
        <DaemonStatus />
      </NavbarGroup>
    </Navbar>
  );
}
