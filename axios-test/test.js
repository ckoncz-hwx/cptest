const http = require("http");
const axios = require("axios");
const yargs = require("yargs/yargs");
const { hideBin } = require("yargs/helpers");
const argv = yargs(hideBin(process.argv))
  .option("count", {
    alias: "c",
    type: "number",
    default: 1,
  })
  .option("sleep", {
    alias: "s",
    type: "number",
    default: 2,
  })
  .option("url", {
    alias: "u",
    default: "http://localhost:8080",
  }).argv;

const instances = [];
const isonow = new Date().toISOString();

const count = argv.count;
const sleep = argv.sleep;
const baseUrl = argv.url


console.log("count", count);
console.log("sleep", sleep);
console.log("baseUrl", baseUrl);

for (i = 0; i < count; i++) {
  instances.push(
    axios.create({
      httpAgent: new http.Agent({ keepAlive: true }),
    })
  );
}

const cdvUrl = `${baseUrl}/sleep/${sleep}/count/${count}/id/${isonow}`;

Promise.all(instances.map(doTest)).then(() => {
  console.log("DONE");
});

function log(msg, instanceNumber) {
  console.log(`instance ${instanceNumber}: ${msg}`);
}

async function doTest(aInstance, instanceNumber) {
  while (true) {
    log(`requesting ... ${cdvUrl}`, instanceNumber);
    const r = await aInstance.get(cdvUrl + `/instanceid/${instanceNumber}`, {
      headers: { "User-Agent": `axios-instance-${instanceNumber}` },
    });
    log("received.", instanceNumber);

    if (false) {
      log("sleeping ...", instanceNumber);
      await new Promise((resolver) => setTimeout(resolver, 8_000));
      log("slept.", instanceNumber);
    }
  }
}
