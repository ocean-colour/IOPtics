=============================================
Cross-algorithm comparison — gloria_turbid_v3
=============================================

:Sweep: gloria_turbid_v3
:Generated: 2026-07-30T07:41:41Z
:ioptics: 0.0.dev0@799bf87
:bing: 0.0.dev0@f242b0e
:ocpy: @da6dff9
:design_doc: 0.15
:implementation_doc: 0.22

Overview
--------

This is the **Cross-algorithm comparison** for sweep ``gloria_turbid_v3`` — a uniform comparison of the IOP-retrieval algorithms ``expb_pow``, ``expb_pow2``, ``expb_pow2flat``, ``expb_powflex`` on GLORIA. Each algorithm inverts the observed remote-sensing reflectance :math:`R_{rs}(\lambda)` for the inherent optical properties (absorption :math:`a`, backscatter :math:`b_b`, and their phytoplankton / CDOM-detritus / particulate components), and the retrieval is scored against the dataset's truth. The figures and tables below show **retrieval accuracy vs. truth**, **fit quality / closure**, and **model selection** between the algorithms; the interactive scatter lets you drill into any component or trophic stratum. See :doc:`/models` for what each algorithm parameterizes and :doc:`/datasets` for the data + truth. All accuracy metrics are log-space / multiplicative (0 = perfect). The header above stamps the exact code + config versions, so every number is reproducible from the persisted sweep artifacts.

Retrieved vs. true — a(440)
---------------------------

Retrieved vs. true **a** at 440 nm, one point per observation and algorithm on log–log axes. Points on the solid **1:1** line are perfect; the dashed **3:1** and **1:3** guides mark the ±3× envelope. Tight, unbiased scatter along 1:1 is the goal; systematic offset above/below it is over-/under-estimation.

.. figure:: scatter_a_440.png
   :width: 90%

   a at 440 nm, all algorithms.

Retrieved vs. true — bb(555)
----------------------------

Retrieved vs. true **bb** at 555 nm, one point per observation and algorithm on log–log axes. Points on the solid **1:1** line are perfect; the dashed **3:1** and **1:3** guides mark the ±3× envelope. Tight, unbiased scatter along 1:1 is the goal; systematic offset above/below it is over-/under-estimation.

.. figure:: scatter_bb_555.png
   :width: 90%

   bb at 555 nm, all algorithms.

Taylor & Target — a(440)
------------------------

**Taylor** (left/first) and **Target** (right/second) diagrams for :math:`a(440)`, computed in log space. The Taylor diagram places each algorithm by its correlation with truth (azimuth) and normalized standard deviation (radius) — the reference star sits at correlation 1, norm-std 1. The Target diagram plots bias (y) against the sign-carrying unbiased RMSD (x); the closer to the origin, the better.

.. figure:: taylor_a.png
   :width: 90%


.. figure:: target_a.png
   :width: 90%

Model selection (ΔBIC)
----------------------

Cumulative distribution of **ΔBIC** per spectrum for the in-tandem pair. ΔBIC < 0 favors the more complex model (``expb_pow``, k=5); ΔBIC > 0 favors the parsimonious one (``giop``, k=3). The curve shows what fraction of spectra fall either side — i.e. whether the extra two parameters earn their keep. See :doc:`/models`.

.. figure:: dbic_cdf_expb_pow_vs_giop.png
   :width: 90%

Accuracy
--------

Per-(component, reference wavelength) retrieval accuracy for the χ² population: multiplicative **mae**/**bias** and **coverage** (0 = perfect; ``mae`` 0.1 ≈ 10%), the cross-algorithm ranks (``*_rank``, 1 = best), and the head-to-head **win_frac**. ``ref_match`` is the native band actually used (±3 nm).

.. csv-table:: Ref-band accuracy + wins (χ², all strata).
   :file: accuracy_chisq_all.csv
   :header-rows: 1

Quality control
---------------

Fit-quality summary per algorithm: ``frac_not_ok`` (retrievals flagged as failures/QC), the median reduced **χ²ᵥ**, and the χ²ᵥ-based closure fractions (``frac_good`` ≈ 1, ``frac_overfit`` < 1, ``frac_underfit`` > 1, ``frac_qc_fail`` = non-solutions).

.. csv-table:: Fit quality / closure (χ²).
   :file: qc_chisq_all.csv
   :header-rows: 1

Interactive
-----------

Retrieved vs. true, **interactive**: pick the dataset, algorithm, component and trophic stratum, and hover any point for its wavelength and values. (Downsampled for the web; the static panels above summarize the full population.)

.. raw:: html

   
   <script src="https://cdn.bokeh.org/bokeh/release/bokeh-3.9.1.min.js"></script>
   <script src="https://cdn.bokeh.org/bokeh/release/bokeh-gl-3.9.1.min.js"></script>
   <script src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.9.1.min.js"></script>
   <script src="https://cdn.bokeh.org/bokeh/release/bokeh-tables-3.9.1.min.js"></script>
   <script src="https://cdn.bokeh.org/bokeh/release/bokeh-mathjax-3.9.1.min.js"></script>
   <script>
   Bokeh.set_log_level("info");
   </script>
   
   <div id="df927509-3a4e-4cbd-8406-a0bddd347fa7" data-root-id="p1067" style="display: contents;"></div>
   <script>
   (function() {
     const fn = function() {
       Bokeh.safely(function() {
         (function(root) {
           function embed_document(root) {
           const docs_json = '{"b852e1a2-edf9-45e5-9ce9-dd2df3eccd7a":{"version":"3.9.1","title":"Bokeh Application","config":{"type":"object","name":"DocumentConfig","id":"p1068","attributes":{"notifications":{"type":"object","name":"Notifications","id":"p1069"}}},"roots":[{"type":"object","name":"Column","id":"p1067","attributes":{"children":[{"type":"object","name":"Select","id":"p1062","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"type":"object","name":"CustomJS","id":"p1066","attributes":{"args":{"type":"map","entries":[["full",{"type":"object","name":"ColumnDataSource","id":"p1006","attributes":{"selected":{"type":"object","name":"Selection","id":"p1007","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1008"},"data":{"type":"map","entries":[["x",[0.72385728,2.53284360229345,0.6661,0.72385728,2.53284360229345,0.6661,0.72385728,2.53284360229345,0.6661,0.72385728,0.72385728,2.53284360229345,0.6661,0.72385728,2.53284360229345,0.6661,0.72385728,2.53284360229345,0.6661,0.72385728]],["y",[0.879680614097329,0.4231718408510084,0.06739655794439631,0.604912107225854,0.9783883433330861,0.2826198159707469,0.901889056628169,0.48006614015858917,0.23052551730965734,0.7232255122345683,0.879680614097329,0.4231718408510084,0.06739655794439631,0.604912107225854,0.9783883433330861,0.2826198159707469,0.901889056628169,0.48006614015858917,0.23052551730965734,0.7232255122345683]],["dataset",["GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA","GLORIA"]],["algorithm",["expb_pow","expb_powflex","expb_powflex","expb_powflex","expb_pow2flat","expb_pow2flat","expb_pow2flat","expb_pow2","expb_pow2","expb_pow2","expb_pow","expb_powflex","expb_powflex","expb_powflex","expb_pow2flat","expb_pow2flat","expb_pow2flat","expb_pow2","expb_pow2","expb_pow2"]],["component",["a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg","a_dg"]],["stratum",["all","all","all","all","all","all","all","all","all","all","eutrophic","unknown","eutrophic","eutrophic","unknown","eutrophic","eutrophic","unknown","eutrophic","eutrophic"]],["wavelength",[440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0,440.0]]]}}}],["src",{"type":"object","name":"ColumnDataSource","id":"p1009","attributes":{"selected":{"type":"object","name":"Selection","id":"p1010","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1011"},"data":{"type":"map","entries":[["x",[0.72385728]],["y",[0.879680614097329]],["dataset",["GLORIA"]],["algorithm",["expb_pow"]],["component",["a_dg"]],["stratum",["all"]],["wavelength",[440.0]]]}}}],["selD",{"id":"p1062"}],["selA",{"type":"object","name":"Select","id":"p1063","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1066"}]]]},"title":"algorithm","options":["expb_pow","expb_pow2","expb_pow2flat","expb_powflex"],"value":"expb_pow"}}],["selC",{"type":"object","name":"Select","id":"p1064","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1066"}]]]},"title":"component","options":["a_dg"],"value":"a_dg"}}],["selS",{"type":"object","name":"Select","id":"p1065","attributes":{"js_property_callbacks":{"type":"map","entries":[["change:value",[{"id":"p1066"}]]]},"title":"stratum","options":["all","eutrophic","unknown"],"value":"all"}}]]},"code":"\\n    const d = full.data;\\n    const o = {&#x27;x&#x27;: [], &#x27;y&#x27;: [], &#x27;dataset&#x27;: [], &#x27;algorithm&#x27;: [], &#x27;component&#x27;: [], &#x27;stratum&#x27;: [], &#x27;wavelength&#x27;: []};\\n    for (let i = 0; i &lt; d[&#x27;algorithm&#x27;].length; i++) {\\n      if (d[&#x27;dataset&#x27;][i] === selD.value\\n          &amp;&amp; d[&#x27;algorithm&#x27;][i] === selA.value\\n          &amp;&amp; d[&#x27;component&#x27;][i] === selC.value\\n          &amp;&amp; d[&#x27;stratum&#x27;][i] === selS.value) {\\n    o[&#x27;x&#x27;].push(d[&#x27;x&#x27;][i]);\\n    o[&#x27;y&#x27;].push(d[&#x27;y&#x27;][i]);\\n    o[&#x27;dataset&#x27;].push(d[&#x27;dataset&#x27;][i]);\\n    o[&#x27;algorithm&#x27;].push(d[&#x27;algorithm&#x27;][i]);\\n    o[&#x27;component&#x27;].push(d[&#x27;component&#x27;][i]);\\n    o[&#x27;stratum&#x27;].push(d[&#x27;stratum&#x27;][i]);\\n    o[&#x27;wavelength&#x27;].push(d[&#x27;wavelength&#x27;][i]);\\n      }\\n    }\\n    src.data = o;\\n    src.change.emit();\\n    "}}]]]},"title":"dataset","options":["GLORIA"],"value":"GLORIA"}},{"id":"p1063"},{"id":"p1064"},{"id":"p1065"},{"type":"object","name":"Figure","id":"p1012","attributes":{"width":560,"height":520,"x_range":{"type":"object","name":"DataRange1d","id":"p1013"},"y_range":{"type":"object","name":"DataRange1d","id":"p1014"},"x_scale":{"type":"object","name":"LogScale","id":"p1022"},"y_scale":{"type":"object","name":"LogScale","id":"p1023"},"title":{"type":"object","name":"Title","id":"p1015","attributes":{"text":"Retrieved vs. true"}},"renderers":[{"type":"object","name":"GlyphRenderer","id":"p1049","attributes":{"data_source":{"id":"p1009"},"view":{"type":"object","name":"CDSView","id":"p1050","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1051"}}},"glyph":{"type":"object","name":"Scatter","id":"p1046","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"size":{"type":"value","value":6},"line_color":{"type":"value","value":"#1f77b4"},"line_alpha":{"type":"value","value":0.6},"fill_color":{"type":"value","value":"#1f77b4"},"fill_alpha":{"type":"value","value":0.6},"hatch_alpha":{"type":"value","value":0.6}}},"nonselection_glyph":{"type":"object","name":"Scatter","id":"p1047","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"size":{"type":"value","value":6},"line_color":{"type":"value","value":"#1f77b4"},"line_alpha":{"type":"value","value":0.1},"fill_color":{"type":"value","value":"#1f77b4"},"fill_alpha":{"type":"value","value":0.1},"hatch_alpha":{"type":"value","value":0.1}}},"muted_glyph":{"type":"object","name":"Scatter","id":"p1048","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"size":{"type":"value","value":6},"line_color":{"type":"value","value":"#1f77b4"},"line_alpha":{"type":"value","value":0.2},"fill_color":{"type":"value","value":"#1f77b4"},"fill_alpha":{"type":"value","value":0.2},"hatch_alpha":{"type":"value","value":0.2}}}}},{"type":"object","name":"GlyphRenderer","id":"p1058","attributes":{"data_source":{"type":"object","name":"ColumnDataSource","id":"p1052","attributes":{"selected":{"type":"object","name":"Selection","id":"p1053","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1054"},"data":{"type":"map","entries":[["x",[0.06739655794439631,2.53284360229345]],["y",[0.06739655794439631,2.53284360229345]]]}}},"view":{"type":"object","name":"CDSView","id":"p1059","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1060"}}},"glyph":{"type":"object","name":"Line","id":"p1055","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"gray","line_dash":[6]}},"nonselection_glyph":{"type":"object","name":"Line","id":"p1056","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"gray","line_alpha":0.1,"line_dash":[6]}},"muted_glyph":{"type":"object","name":"Line","id":"p1057","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"line_color":"gray","line_alpha":0.2,"line_dash":[6]}}}}],"toolbar":{"type":"object","name":"Toolbar","id":"p1021","attributes":{"tools":[{"type":"object","name":"PanTool","id":"p1034"},{"type":"object","name":"BoxZoomTool","id":"p1035","attributes":{"dimensions":"both","overlay":{"type":"object","name":"BoxAnnotation","id":"p1036","attributes":{"syncable":false,"line_color":"black","line_alpha":1.0,"line_width":2,"line_dash":[4,4],"fill_color":"lightgrey","fill_alpha":0.5,"level":"overlay","visible":false,"left":{"type":"number","value":"nan"},"right":{"type":"number","value":"nan"},"top":{"type":"number","value":"nan"},"bottom":{"type":"number","value":"nan"},"left_units":"canvas","right_units":"canvas","top_units":"canvas","bottom_units":"canvas","handles":{"type":"object","name":"BoxInteractionHandles","id":"p1042","attributes":{"all":{"type":"object","name":"AreaVisuals","id":"p1041","attributes":{"fill_color":"white","hover_fill_color":"lightgray"}}}}}}}},{"type":"object","name":"WheelZoomTool","id":"p1043","attributes":{"renderers":"auto"}},{"type":"object","name":"ResetTool","id":"p1044"},{"type":"object","name":"SaveTool","id":"p1045"},{"type":"object","name":"HoverTool","id":"p1061","attributes":{"renderers":"auto","tooltips":[["algorithm","@algorithm"],["component","@component"],["\\u03bb","@wavelength"],["truth","@x"],["retrieved","@y"]],"sort_by":null}}]}},"left":[{"type":"object","name":"LogAxis","id":"p1029","attributes":{"ticker":{"type":"object","name":"LogTicker","id":"p1030","attributes":{"num_minor_ticks":10,"mantissas":[1,5]}},"formatter":{"type":"object","name":"LogTickFormatter","id":"p1031"},"axis_label":"retrieved","major_label_policy":{"type":"object","name":"AllLabels","id":"p1032"}}}],"below":[{"type":"object","name":"LogAxis","id":"p1024","attributes":{"ticker":{"type":"object","name":"LogTicker","id":"p1025","attributes":{"num_minor_ticks":10,"mantissas":[1,5]}},"formatter":{"type":"object","name":"LogTickFormatter","id":"p1026"},"axis_label":"truth","major_label_policy":{"type":"object","name":"AllLabels","id":"p1027"}}}],"center":[{"type":"object","name":"Grid","id":"p1028","attributes":{"axis":{"id":"p1024"}}},{"type":"object","name":"Grid","id":"p1033","attributes":{"dimension":1,"axis":{"id":"p1029"}}}]}}]}}]}}';
           const render_items = [{"docid":"b852e1a2-edf9-45e5-9ce9-dd2df3eccd7a","roots":{"p1067":"df927509-3a4e-4cbd-8406-a0bddd347fa7"},"root_ids":["p1067"]}];
           root.Bokeh.embed.embed_items(docs_json, render_items);
           }
           if (root.Bokeh !== undefined) {
             embed_document(root);
           } else {
             let attempts = 0;
             const timer = setInterval(function(root) {
               if (root.Bokeh !== undefined) {
                 clearInterval(timer);
                 embed_document(root);
               } else {
                 attempts++;
                 if (attempts > 100) {
                   clearInterval(timer);
                   console.log("Bokeh: ERROR: Unable to run BokehJS code because BokehJS library is missing");
                 }
               }
             }, 10, root)
           }
         })(window);
       });
     };
     if (document.readyState != "loading") fn();
     else document.addEventListener("DOMContentLoaded", fn);
   })();
   </script>
