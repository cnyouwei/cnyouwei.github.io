export default {
  initialize: function () {},
  run: async function ({nodes}) {
    for (const node of nodes) {
      node.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 30" role="img" aria-label="Test diagram"><text x="0" y="20">Test diagram</text></svg>';
      node.setAttribute('data-processed', 'true');
    }
  }
};
