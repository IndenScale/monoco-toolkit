#!/usr/bin/env node

const { program } = require("commander");
const open = require("open");
const path = require("path");
const polka = require("polka");
const sirv = require("sirv");

program
  .name("monoco-kanban")
  .description("Launch the Monoco Kanban Board")
  .version("0.1.0")
  .option("-p, --port <number>", "port to run the board on", "3123")
  .option("-h, --host <string>", "host to run the board on", "127.0.0.1")
  .option("--no-open", "do not open the browser automatically")
  .action(async (options) => {
    const distPath = path.resolve(__dirname, "../dist");
    const port = parseInt(options.port, 10);
    const host = options.host;
    const url = `http://${host}:${port}`;

    console.log(`\n🚀 Monoco Kanban Board`);
    console.log(`------------------------`);
    console.log(`Serving from: ${distPath}`);
    console.log(`URL: ${url}\n`);

    const assets = sirv(distPath, {
      single: true,
      dev: false,
    });

    polka()
      .use(assets)
      .listen(port, host, (err) => {
        if (err) {
          console.error(`❌ Failed to start server: ${err.message}`);
          process.exit(1);
        }

        if (options.open) {
          console.log(`Opening browser...`);
          open(url);
        }

        console.log(`Press Ctrl+C to stop.\n`);
      });
  });

program.parse();
