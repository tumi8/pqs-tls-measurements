---
layout: page
permalink: /setup/
title: "Hardware Setup"
description: "This page describes the 3-node hardware timestamping setup used for our experiments. To make our artifacts available to a broad community, we converted all our scripts to run in a containerized 2-node environment that should provide similar results."
---


<h3>Network Topology</h3>
<p><img src="{{site.baseurl}}/figures/setup.pdf.svg" style="display:block;margin-left:auto;margin-right:auto;width=90%;" width="500pt" alt="network topology"/></p>


<h3>Hardware</h3>

<p>All tree nodes are equipped with identical hardware consisting of:</p>

<ul>
	<li>SoC: Intel Xeon D-1518 CPU</li>
	<li>Dual port Intel X552 NIC (10G Ethernet)</li>
	<li>32 GiB RAM</li>
</ul>

<p>An optical splitter connects the timestamper with the link between the client and the server.</p>

<h3>Docker Setup for Evaluation and simplified experiments</h3>

<p>We prepared a Docker setup with two containers to repeat of our experiments in arbitrary environments. Caution: The results and precision is different compared to our hardware setup, although, the trends between different PQ variants we have shown in the paper should remain the same. It is available in our Github repository and has no special requirements: <a href="https://github.com/tumi8/pqs-tls-measurements/tree/main/code">Github Repository</a>. How to use it will be described on this website for the different types of results.</p>
          